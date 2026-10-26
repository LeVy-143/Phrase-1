# Tests
Chạy `.venv/bin/python -m pytest -q` hoặc eval runner.
Behavioral cases: test_evals.py; protocol mock: test_provider.py;
Streamlit AppTest (có cả trọn 11 câu): test_app.py.
Tất cả dùng DB tạm, tài khoản giả, đồng hồ tiêm cho timer; không dùng key/network.
Fixture band 6 chỉ là expected value của unit test, không là kết quả chấm của model.
