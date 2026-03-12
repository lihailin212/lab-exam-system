# 医学实验室在线考核系统

一个适用于医学实验室的在线考核系统，支持扫码登录、自定义考核、自动判分、成绩统计等功能。

## 功能特性

- ✅ 工号密码登录（支持扫码）
- ✅ 自定义考核时间和题目
- ✅ 支持单选题、多选题、判断题
- ✅ 图文题目（富文本编辑器）
- ✅ 批量导入题目（支持 Excel、Word、TXT 格式）
- ✅ 自动判分
- ✅ 成绩统计与图表展示
- ✅ 移动端和PC端自适应

## 技术栈

- **前端**: Vue 3 + Element Plus + Vant + ECharts
- **后端**: Python + FastAPI + SQLite
- **部署**: Vercel (前端) + Render (后端)

## 快速开始

### 本地开发

1. **克隆项目**
```bash
git clone <your-repo-url>
cd lab-exam-system
```

2. **启动后端**
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

3. **启动前端**
```bash
cd frontend
npm install
npm run dev
```

4. **访问系统**
- 前端: http://localhost:3000
- 后端API: http://localhost:8000
- API文档: http://localhost:8000/docs

### 默认账号

- 管理员: admin / admin123
- 员工: 需要在管理后台添加

## 批量导入题目

### 支持格式

| 格式 | 文件扩展名 | 说明 |
|------|------------|------|
| Excel | .xlsx, .xls | 推荐使用 |
| Word | .docx | 表格格式 |
| TXT/CSV | .txt, .csv | 逗号分隔 |

### 导入模板格式

Excel/Word 表头格式：
| 题型 | 题干 | 选项 | 答案 | 解析 | 分值 |
|------|------|------|------|------|------|
| single | 题目内容 | A:选项1\|B:选项2\|C:选项3\|D:选项4 | A | 解析内容 | 10 |

TXT/CSV 格式（逗号分隔）：
```
single,题目内容,A:选项1|B:选项2|C:选项3|D:选项4,A,解析内容,10
```

### 题型说明

- `single` - 单选题
- `multiple` - 多选题
- `judgment` - 判断题

### 使用方法

1. 进入管理后台 → 考核管理 → 选择考核
2. 点击"批量导入"按钮
3. 点击"下载导入模板"获取模板文件
4. 按模板格式填写题目
5. 上传文件并点击"开始导入"

## 部署指南

### 后端部署 (Render)

1. 将代码推送到GitHub
2. 登录 [Render](https://render.com)
3. 创建新的 Web Service
4. 选择 GitHub 仓库
5. 配置:
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
6. 部署完成后获取后端URL

### 前端部署 (Vercel)

1. 将代码推送到GitHub
2. 登录 [Vercel](https://vercel.com)
3. 导入 GitHub 仓库
4. 配置:
   - Framework Preset: Vite
   - Build Command: `npm run build`
   - Output Directory: `dist`
5. 部署完成后获取前端URL

### 配置二维码

1. 部署完成后，将前端URL生成二维码
2. 使用[草料二维码](https://cli.im)生成登录二维码
3. 员工扫码即可访问

## 项目结构

```
lab-exam-system/
├── backend/           # 后端项目
│   ├── app/
│   │   ├── main.py    # FastAPI入口
│   │   ├── models.py  # 数据模型
│   │   ├── schemas.py # Pydantic schemas
│   │   ├── crud.py    # 数据库操作
│   │   ├── auth.py    # JWT认证
│   │   └── routers/   # API路由
│   └── requirements.txt
├── frontend/          # 前端项目
│   ├── src/
│   │   ├── views/     # 页面组件
│   │   ├── api/       # API调用
│   │   ├── stores/    # Pinia状态
│   │   └── router/    # 路由配置
│   └── package.json
└── README.md
```

## License

MIT
