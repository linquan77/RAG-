FROM python:3.11-slim

WORKDIR /app

# 先装依赖（利用缓存层，代码改动不会重新装包）
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
    -i https://pypi.tuna.tsinghua.edu.cn/simple \
    --trusted-host pypi.tuna.tsinghua.edu.cn

# 再复制代码
COPY . .

# 创建文档目录
RUN mkdir -p /app/docs

EXPOSE 8501

CMD ["streamlit", "run", "app.py", "--server.address=0.0.0.0"]