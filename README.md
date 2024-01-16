# personal_finance_management_chatbot

+-----------------+                +---------------------+               +-------------------+
|    Client       |                |      Chatbot        |               |      Server       |
|-----------------|                |---------------------|               |-------------------|
|                 |                |                     |               |                   |
|  Telegram App   |                |    Python Script    |               |  SQLite Database  |
|                 |                |                     |               |                   |
+--------+--------+                +---------------------+               +---------+---------+
         |                                                                         |
         |              /start, /set, /update, /check, /history, /reset            |
         +-------------------------------------------------------------------------+
                                      |
                                      |
                                      |      Handle Commands and Messages
                                      |
                                      v
                              +----------------------+
                              |    Python Functions  |
                              |----------------------|
                              |  Database Operations |
                              |  Expense Management  |
                              +----------------------+

1. Client (Telegram App): Người dùng tương tác với chatbot thông qua Telegram App.

2. Chatbot (Python Script): Bot chạy trên máy chủ và sử dụng thư viện Telegram để tương tác với người dùng. Nó chứa các hàm xử lý lệnh và thông điệp từ người dùng.

3. Server (SQLite Database): Dữ liệu người dùng được lưu trữ trong cơ sở dữ liệu SQLite trên máy chủ. Các hàm xử lý dữ liệu của người dùng được thực hiện thông qua các truy vấn SQL.

Các tương tác chính:

- Người dùng gửi lệnh hoặc tin nhắn văn bản.
- Chatbot xử lý lệnh hoặc tin nhắn từ người dùng, thực hiện các hàm tương ứng.
- Chatbot thực hiện các truy vấn cơ sở dữ liệu để lưu trữ và truy xuất thông tin về ngân sách và lịch sử chi tiêu của người dùng.
