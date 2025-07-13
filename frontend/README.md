# Flag Guard System Frontend

## ��Ŀ����

Flag Guard System ǰ���ǻ��� Vue 3 + TypeScript �������ִ�����ҳӦ��(SPA)��ΪУѧ�����커���ӹ���ϵͳ�ṩֱ�۵��û����档

## ����ջ

- **���**: Vue 3 (Composition API)
- **����**: TypeScript
- **UI��**: Element Plus + Element Plus Icons
- **״̬����**: Pinia
- **·��**: Vue Router 4
- **HTTP�ͻ���**: Axios
- **��������**: Vue CLI 5
- **����淶**: ESLint + TypeScript ESLint

## ����ģ��

### ����ҳ��
- **��¼/ע��** (`Login.vue`, `Register.vue`) - �û���֤
- **�Ǳ���** (`Dashboard.vue`) - ���ݸ�����ͳ��
- **��������** (`Profile.vue`) - �û���Ϣ����

### �û�����
- **�û��б�** (`Users.vue`) - �û��鿴�͹���

### ѵ������
- **ѵ���б�** (`Trainings.vue`) - ѵ���ƻ��鿴�͹���
- **ѵ������** (`TrainingAttendance.vue`) - ���ڼ�¼����
- **ѵ�����** (`TrainingReview.vue`) - ѵ���������

### �����
- **��б�** (`Events.vue`) - ��鿴�Ͳ���
- **�����** (`EventManage.vue`) - ������ͱ༭

### ���������
- **�������¼** (`FlagRecords.vue`) - ��¼�鿴
- **���������** (`FlagReview.vue`) - �������

### ����ϵͳ
- **���ּ�¼** (`Points.vue`) - ������ʷ�鿴
- **���ֹ���** (`PointsManage.vue`) - ���ֵ�����ͳ��

## ��Ŀ�ṹ

```
src/
������ App.vue              # �����
������ main.ts              # Ӧ�����
������ shims-vue.d.ts       # Vue TypeScript ����
������ env.d.ts             # ����������������
������ assets/              # ��̬��Դ
��   ������ login-bg.jpg     # ��¼����ͼ
������ components/          # �ɸ������
��   ������ ECharts.vue      # ͼ�����
������ layout/              # �������
��   ������ index.vue        # ������
������ router/              # ·������
��   ������ index.ts         # ·�ɶ���
������ stores/              # Pinia ״̬����
��   ������ dashboard.ts     # �Ǳ���״̬
��   ������ event.ts         # �״̬
��   ������ training.ts      # ѵ��״̬
��   ������ user.ts          # �û�״̬
������ styles/              # ȫ����ʽ
��   ������ index.css        # ��ʽ����
������ types/               # TypeScript ���Ͷ���
��   ������ api.ts           # API �ӿ�����
��   ������ element-plus.d.ts # Element Plus ������չ
��   ������ env.d.ts         # ��������
��   ������ training.ts      # ѵ���������
������ utils/               # ���ߺ���
��   ������ format.ts        # ���ݸ�ʽ��
��   ������ formatDate.ts    # ���ڸ�ʽ��
��   ������ request.ts       # HTTP �����װ
������ views/               # ҳ�����
    ������ 404.vue          # 404 ����ҳ
    ������ Dashboard.vue    # �Ǳ���
    ������ EventManage.vue  # �����
    ������ Events.vue       # ��б�
    ������ FlagRecords.vue  # �������¼
    ������ FlagReview.vue   # ���������
    ������ Login.vue        # ��¼ҳ
    ������ Points.vue       # ���ּ�¼
    ������ PointsManage.vue # ���ֹ���
    ������ Profile.vue      # ��������
    ������ Records.vue      # ��¼ҳ��
    ������ Register.vue     # ע��ҳ
    ������ TrainingAttendance.vue # ѵ������
    ������ TrainingReview.vue     # ѵ�����
    ������ Trainings.vue    # ѵ���б�
    ������ Users.vue        # �û�����
```

## ������������

### ��װ����
```bash
npm install
```

### ��������������
```bash
npm run serve
```
�������������� `http://localhost:8080` ������֧�������ء�

### ���������汾
```bash
npm run build
```

### ��������޸�
```bash
npm run lint
```

## ��������

### ·��Ȩ�޿���
- �����û���ɫ��·������
- ֧�� member��admin��captain��superadmin ��ɫ
- ��̬�˵�����

### ״̬����
- ʹ�� Pinia ����״̬����
- ģ�黯��ƣ��û����Ǳ��̡����ѵ��״̬����
- ���ݳ־û�֧��

### HTTP ����
- Axios ���η�װ��֧������/��Ӧ����
- �Զ� JWT Token ����
- ͳһ���������ʾ

### UI ���
- Element Plus �����
- ��Ӧʽ���֧��
- �Զ���������ʽ

### TypeScript ֧��
- ���������Ͷ���
- API �ӿ����Ͱ�ȫ
- ����ʱ���ͼ��

## ����˵��

### ��������
��Ŀ֧��ͨ�������������ú�� API ��ַ����Ϣ��

### ��������
���������£�ǰ�˴��������� `vue.config.js` �����ã����ڽ���������⡣

## ���֤

MIT License
