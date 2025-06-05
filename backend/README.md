# У���커���ӹ���ϵͳ���

## ��Ŀ˵��
����һ������ Flask ��У���커���ӹ���ϵͳ��ˣ��ṩ�û����������ѵ�������������¼�ȹ��ܡ�

## ��������
- �û���֤����Ȩ
- �����
- ѵ������
- �������¼
- ����ϵͳ
- �ļ��ϴ�
- API �ĵ���Swagger��

## ����ջ
- Python 3.8+
- Flask
- SQLAlchemy
- JWT
- Swagger

## ��װ˵��

1. ��¡��Ŀ
```bash
git clone <repository-url>
cd backend
```

2. �������⻷��
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

3. ��װ����
```bash
pip install -r requirements.txt
```

4. ���û�������
���� `.env.example` Ϊ `.env` ���޸����ã�
```bash
cp .env.example .env
```

5. ��ʼ�����ݿ�
```bash
flask init-db
```

6. ��������Ա�û�
```bash
flask create-admin <username> <password> <name> <student_id>
```

## ������Ŀ

1. ��������������
```bash
flask run
```

2. ���� API �ĵ�
```
http://localhost:5000/apidocs
```

## �����й���

ϵͳ�ṩ���������й��ߣ�

- `flask init-db`: ��ʼ�����ݿ�
- `flask drop-db`: ɾ���������ݿ��
- `flask create-admin`: ��������Ա�û�
- `flask list-users`: �г������û�
- `flask cleanup-records`: ����ɼ�¼
- `flask backup-db`: �������ݿ�
- `flask check-system`: ���ϵͳ״̬
- `flask reset-password`: �����û�����
- `flask export-data`: ����ϵͳ����

## ��Ŀ�ṹ
```
backend/
������ app.py              # Ӧ�����
������ config.py           # �����ļ�
������ extensions.py       # Flask��չ
������ models.py           # ����ģ��
������ cli.py             # �����й���
������ requirements.txt    # ��Ŀ����
������ .env               # ��������
������ routes/            # ·��ģ��
������ utils/             # ���ߺ���
������ middleware/        # �м��
������ uploads/           # �ϴ��ļ�Ŀ¼
������ logs/              # ��־Ŀ¼
```

## ����ָ��

1. ������
- ʹ�� Black ���д����ʽ��
- ʹ�� Flake8 ���д�����

2. ����
```bash
pytest
```

3. ���ݿ�Ǩ��
```bash
flask db migrate -m "migration message"
flask db upgrade
```

## ����˵��

1. ������������
- �޸� `.env` �ļ��еĻ�������
- ���� `FLASK_ENV=production`
- �������ݿ�����
- ���ð�ȫ����Կ

2. ʹ�� Gunicorn ����
```bash
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

## ����ָ��

1. Fork ��Ŀ
2. �������Է�֧
3. �ύ����
4. ���͵���֧
5. ���� Pull Request

## ���֤
MIT License 