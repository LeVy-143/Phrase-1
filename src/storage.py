"""SQLite checkpoints, ownership, CAS and atomic idempotency."""
import copy
from contextlib import contextmanager
import json
import sqlite3
from pathlib import Path
from pydantic import TypeAdapter, ValidationError as SchemaError
from .contracts import SessionState
from .errors import AccessDenied, NotFound, RevisionConflict, IdempotencyConflict, ValidationError, StorageError

class Storage:
    def __init__(self, db_path: Path) -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.initialize()

    @contextmanager
    def connect(self):
        db=None
        try:
            db=sqlite3.connect(self.db_path,timeout=10)
            db.row_factory=sqlite3.Row
            db.execute('PRAGMA foreign_keys=ON')
            with db:
                yield db
        except sqlite3.Error:
            raise StorageError('SQLite operation failed; check database permissions and free space') from None
        finally:
            if db is not None:
                db.close()

    def initialize(self):
        with self.connect() as db:
            db.executescript('''
            CREATE TABLE IF NOT EXISTS sessions (
              session_id TEXT PRIMARY KEY, learner_id TEXT NOT NULL,
              revision INTEGER NOT NULL, state_json TEXT NOT NULL, updated_at TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS assessments (
              assessment_id TEXT PRIMARY KEY, session_id TEXT NOT NULL UNIQUE
              REFERENCES sessions(session_id) ON DELETE CASCADE, result_json TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS requests (
              session_id TEXT REFERENCES sessions(session_id) ON DELETE CASCADE,
              request_id TEXT, payload_hash TEXT NOT NULL, reply_json TEXT NOT NULL,
              PRIMARY KEY(session_id, request_id));
            CREATE TABLE IF NOT EXISTS retrievals (
              session_id TEXT REFERENCES sessions(session_id) ON DELETE CASCADE,
              chunk_id TEXT, chunk_json TEXT NOT NULL, PRIMARY KEY(session_id,chunk_id));
            CREATE TABLE IF NOT EXISTS traces (
              event_id TEXT PRIMARY KEY, session_id TEXT REFERENCES sessions(session_id)
              ON DELETE CASCADE, event_json TEXT NOT NULL);
            ''')

    def _owned(self, db, session_id, context):
        row = db.execute('SELECT * FROM sessions WHERE session_id=?', (session_id,)).fetchone()
        if row is None:
            raise NotFound('Session not found')
        if row['learner_id'] != context['learner_id'] or session_id != context['session_id']:
            raise AccessDenied('Session not available to this learner')
        state = json.loads(row['state_json'])
        if state['run_id'] != context['run_id']:
            raise AccessDenied('Run context does not match')
        return row

    def save_session(self, state, *, expected_revision, context):
        return self.commit_reply({'state': state, 'examiner_message': '', 'assessment': None},
                                 expected_revision=expected_revision, context=context)['state']

    def commit_reply(self, reply, *, expected_revision, context, request_id=None, payload_hash=None):
        reply = copy.deepcopy(reply)
        state = reply['state']
        try:
            TypeAdapter(SessionState).validate_python(state, strict=True)
        except SchemaError:
            raise ValidationError('Invalid session state schema') from None
        if state['learner_id'] != context['learner_id'] or state['session_id'] != context['session_id'] or state['run_id'] != context['run_id']:
            raise AccessDenied('Invalid write context')
        with self.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            if request_id is not None:
                existing = self._cached(db, context, request_id, payload_hash)
                if existing is not None:
                    return existing
            if expected_revision is None:
                if db.execute('SELECT 1 FROM sessions WHERE session_id=?', (state['session_id'],)).fetchone():
                    raise RevisionConflict('Session already exists')
                state['revision'] = 1
                db.execute('INSERT INTO sessions VALUES (?,?,?,?,?)', (state['session_id'], state['learner_id'], 1, json.dumps(state), state['updated_at']))
            else:
                row = self._owned(db, state['session_id'], context)
                if row['revision'] != expected_revision:
                    raise RevisionConflict('Reload the latest session before submitting')
                state['revision'] = expected_revision + 1
                db.execute('UPDATE sessions SET revision=?,state_json=?,updated_at=? WHERE session_id=?',
                           (state['revision'], json.dumps(state), state['updated_at'], state['session_id']))
            assessment = reply.get('assessment')
            if assessment:
                if assessment['session_id'] != state['session_id'] or assessment['run_id'] != state['run_id']:
                    raise ValidationError('Assessment context mismatch')
                from .tools import validate_assessment
                snapshots=[json.loads(r[0]) for r in db.execute('SELECT chunk_json FROM retrievals WHERE session_id=?',(state['session_id'],))]
                validate_assessment(assessment,state=state,retrieved=snapshots)
                db.execute('INSERT INTO assessments VALUES (?,?,?)',
                           (assessment['assessment_id'], state['session_id'], json.dumps(assessment)))
            if request_id is not None:
                db.execute('INSERT INTO requests VALUES (?,?,?,?)',
                           (state['session_id'], request_id, payload_hash, json.dumps(reply)))
        return reply

    def _cached(self, db, context, request_id, payload_hash):
        row = db.execute('SELECT payload_hash,reply_json FROM requests WHERE session_id=? AND request_id=?',
                         (context['session_id'], request_id)).fetchone()
        if row:
            self._owned(db, context['session_id'], context)
            if row['payload_hash'] != payload_hash:
                raise IdempotencyConflict('Request ID was already used for a different payload')
            return json.loads(row['reply_json'])
        return None

    def cached_reply(self, context, request_id, payload_hash):
        with self.connect() as db:
            self._owned(db, context['session_id'], context)
            return self._cached(db, context, request_id, payload_hash)

    def load_session(self, session_id, *, context):
        with self.connect() as db:
            return json.loads(self._owned(db, session_id, context)['state_json'])

    def list_sessions(self, learner_id):
        with self.connect() as db:
            return [json.loads(row[0]) for row in db.execute('SELECT state_json FROM sessions WHERE learner_id=? ORDER BY updated_at DESC', (learner_id,))]

    def record_retrieval(self, chunks, *, context):
        with self.connect() as db:
            self._owned(db,context['session_id'],context)
            for chunk in chunks:
                db.execute('INSERT OR IGNORE INTO retrievals VALUES (?,?,?)',
                           (context['session_id'],chunk['chunk_id'],json.dumps(chunk)))

    def save_assessment(self, assessment, *, context):
        state=self.load_session(context['session_id'],context=context)
        if assessment['session_id'] != state['session_id'] or assessment['run_id'] != state['run_id']:
            raise ValidationError('Assessment context mismatch')
        if state['status'] != 'awaiting_assessment':
            raise ValidationError('Assessment requires a completed interview')
        state['status']='completed'
        self.commit_reply({'state':state,'examiner_message':'','assessment':assessment},
                          expected_revision=state['revision'],context=context)

    def checkpoint(self, *, context, expected_revision):
        # Real database write, preserving the logical state revision. The model
        # receives only an acknowledgement, never arbitrary SQL or write access.
        with self.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            row=self._owned(db,context['session_id'],context)
            if row['revision'] != expected_revision:
                raise RevisionConflict('Checkpoint revision changed')
            db.execute('UPDATE sessions SET state_json=? WHERE session_id=? AND revision=?',
                       (row['state_json'],context['session_id'],expected_revision))
        return {'persisted':True,'revision':expected_revision,'session_id':context['session_id']}

    def purge_traces(self, before_iso):
        with self.connect() as db:
            return db.execute("DELETE FROM traces WHERE json_extract(event_json,'$.timestamp')<?",(before_iso,)).rowcount

    def load_assessment(self, session_id, *, context):
        with self.connect() as db:
            self._owned(db, session_id, context)
            row = db.execute('SELECT result_json FROM assessments WHERE session_id=?', (session_id,)).fetchone()
            return json.loads(row[0]) if row else None

    def delete_learner_data(self, learner_id, *, context):
        if learner_id != context['learner_id']:
            raise AccessDenied('Cannot delete another learner')
        with self.connect() as db:
            db.execute('DELETE FROM sessions WHERE learner_id=?', (learner_id,))

    def purge(self, before_iso):
        with self.connect() as db:
            return db.execute('DELETE FROM sessions WHERE updated_at<?', (before_iso,)).rowcount

    def trace(self, event, *, context):
        # All event values are references/metrics, never raw model or candidate content.
        allowed = {'event_id','run_id','session_id','timestamp','event_type','name',
                   'input_refs','output_refs','duration_ms','token_count','estimated_cost',
                   'currency','error_code','model','prompt_version','data_version','descriptor_version','arguments','succeeded'}
        if set(event) - allowed:
            raise ValidationError('Trace contains unsupported fields')
        with self.connect() as db:
            self._owned(db, context['session_id'], context)
            db.execute('INSERT INTO traces VALUES (?,?,?)', (event['event_id'], context['session_id'], json.dumps(event)))

    def load_traces(self, *, context):
        with self.connect() as db:
            self._owned(db, context['session_id'], context)
            return [json.loads(row[0]) for row in db.execute('SELECT event_json FROM traces WHERE session_id=? ORDER BY rowid', (context['session_id'],))]
