# Team-Sys: Уѧ�����커���ӹ���ϵͳ

`Team-Sys` ��һ�������걸��ȫջWebӦ�ã�ּ��ΪУѧ�����커�����ṩһ����Ч��ֱ�۵Ļ���Ա������������ϵͳ�������û�����ѵ���ճ̡����֯�����ּ����Ⱥ���ģ�飬�����ִ����ļ���ջ������ǰ�˻��� Vue.js��������� Flask ������

## ? ���Ĺ���

- **? �û�����**: ���ڽ�ɫ��Ȩ�޿��ƣ���Ա������Ա����������Ա����֧���û���Ϣ����ɾ�Ĳ顣
- **?? ѵ������**: ���ɴ������༭�͹���ѵ���ճ̣�׷�ٳ�Ա�ı����뿼�������
- **? �����**: ��ݵ���֯�Ŷӻ�����ɽ�����ض���ѵ����Ŀ���й�����
- **? ����ϵͳ**: Ϊ����ѵ����������Ȼ���û�������֣������������ơ�
- **? �����Ǳ���**: Ϊ����Ա�ṩϵͳ���ݸ�������������������ڻ�ȣ�ʵ��һվʽ����
- **? RESTful API**: �ṩ���������� API �ӿڣ�ȷ��ǰ�������ͨ�ŵ��ȶ����Ч��

## ?? ����ջ

|              | ����                                                                  |
| ------------ | --------------------------------------------------------------------- |
| **���**     | Python 3, Flask, SQLAlchemy, Flask-Migrate, Flask-JWT-Extended        |
| **ǰ��**     | Vue 3 (Composition API), TypeScript, Element Plus, Pinia, Vue Router, Axios |
| **���ݿ�**   | MySQL                                                                 |
| **��������** | Node.js, npm, pip, virtualenv                                         |

## ? ���ز���ָ��

����ѭ���²��������ı��ػ��������д���Ŀ��

### ׼������

- ȷ�����ĵ����Ѱ�װ [Node.js](https://nodejs.org/) (v16+ �汾)
- ȷ�����ĵ����Ѱ�װ [Python](https://www.python.org/) (v3.8+ �汾)
- ȷ�����ĵ����Ѱ�װ������ [MySQL](https://www.mysql.com/) ����

### ��˷�������

```bash
# 1. ��������ĿĿ¼
cd backend

# 2. ���������� Python ���⻷��
# Windows
python -m venv venv
venv\Scripts\activate

# macOS / Linux
# python3 -m venv venv
# source venv/bin/activate

# 3. ��װ��������
pip install -r requirements.txt

# 4. �������ݿ�����
#    - ���ȣ������� MySQL �д���һ���µ����ݿ� (���� `teamsys_db`)��
#    - Ȼ�󣬴� `backend/config.py` �ļ����޸� `SQLALCHEMY_DATABASE_URI` ��ֵΪ�������ݿ�������Ϣ��
#      ʾ��: 'mysql+pymysql://����û���:�������@127.0.0.1/teamsys_db'

# 5. ��ʼ�����ݿⲢ������������Ա�˺�
#    �뽫 <...> �����滻Ϊ����Ҫ����Ϣ
flask --app backend/app.py drop-db --yes
flask --app backend/app.py init-db
flask --app backend/app.py create-user <�û���> <����> <����> <ѧ��(��:PB23000000)> --role superadmin

# 6. ������˿���������
flask run
```

### ǰ�˷�������

```bash
# 1. ��һ���µ��նˣ�����ǰ����ĿĿ¼
cd frontend

# 2. ��װ��������
npm install

# 3. ����ǰ�˿���������
npm run serve
```

�����в�����ɺ�������ͨ����������� `http://localhost:8080` ���鿴�����е���Ŀ��

## ? ��Ŀ�ṹ

```
system/
������ backend/            # Flask ���Դ����
��   ������ app.py          # Ӧ�����ļ�
��   ������ cli.py          # �Զ��� Flask ����
��   ������ config.py       # �����ļ�
��   ������ models.py       # ���ݿ�ģ��
��   ������ routes/         # API ·����ͼ
������ frontend/           # Vue.js ǰ��Դ����
��   ������ src/
��   ��   ������ components/ # �ɸ������
��   ��   ������ stores/     # Pinia ״̬����
��   ��   ������ views/      # ҳ����ͼ
��   ��   ������ ...
��   ������ package.json
������ README.md           # ���ĵ�
```

## ���֤

MIT 