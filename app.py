import streamlit as st
import tempfile, os
from ingest import ingest
from chain import get_qa_chain
from doc_manager import list_documents, delete_document, clear_all

st.set_page_config(page_title="RAG 知识库问答", page_icon="📚")
st.title("📚 RAG 知识库问答系统")

# 侧边栏：文档上传和管理
with st.sidebar:
    tab1, tab2 = st.tabs(["📂 上传文档", "🗂️ 文档管理"])

    # Tab1：上传
    with tab1:
        uploaded = st.file_uploader(
            "支持 PDF / Word / Excel",
            type=["pdf", "docx", "xlsx"],   # ← 加了 xlsx
            accept_multiple_files=True
        )
        if uploaded and st.button("解析入库", type="primary"):
            for idx, f in enumerate(uploaded):
                st.write(f"📄 处理: {f.name}")
                progress_bar = st.progress(0)
                status_text = st.empty()

                def update_progress(progress: float, status: str):
                    progress_bar.progress(progress)
                    status_text.text(f"状态: {status}")

                with tempfile.NamedTemporaryFile(
                    delete=False,
                    suffix=f".{f.name.split('.')[-1]}"
                ) as tmp:
                    tmp.write(f.read())
                    tmp_path = tmp.name

                count = ingest(tmp_path, original_name=f.name, progress_callback=update_progress)
                os.unlink(tmp_path)

                if count == 0:
                    st.warning(f"{f.name} 已入库，跳过")
                else:
                    st.success(f"{f.name} 已入库，共 {count} 个切块")

    # Tab2：文档管理
    with tab2:
        docs = list_documents()

        if not docs:
            st.info("知识库暂无文档")
        else:
            st.caption(f"共 {len(docs)} 个文档，{sum(d['chunks'] for d in docs)} 个切块")
            st.divider()

            for doc in docs:
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.markdown(f"**{doc['filename']}**")
                    st.caption(f"{doc['chunks']} 个切块")
                with col2:
                    if st.button("删除", key=f"del_{doc['filename']}"):
                        try:
                            n = delete_document(doc["source"])
                            st.success(f"已删除 {n} 个切块")
                            st.rerun()
                        except Exception as e:
                            st.error(f"删除失败：{e}")

            st.divider()
            if st.button("🗑️ 清空全部", type="secondary", use_container_width=True):
                if clear_all():
                    st.success("知识库已清空")
                    st.rerun()


# 主区域：问答
st.header("💬 开始提问")
if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    st.chat_message(msg["role"]).write(msg["content"])

if query := st.chat_input("请输入问题..."):
    st.session_state.messages.append({"role": "user", "content": query})
    st.chat_message("user").write(query)

    with st.chat_message("assistant"):
        with st.spinner("检索中..."):
            chain = get_qa_chain()
            result = chain.invoke(query)
            answer = result["answer"]
            sources = result["sources"]

        st.write(answer)

        if sources:
            with st.expander("📄 查看来源"):
                for doc in sources:
                    source = doc.metadata.get("source", "未知文件")
                    doc_type = doc.metadata.get("type", "")

                    # Excel 价格表显示行号，其他文档显示页码
                    if doc_type in ["price_table", "price_summary"]:
                        row = doc.metadata.get("row", "?")
                        location = f"第 {row} 行" if doc_type == "price_table" else "商品汇总"
                    else:
                        page = doc.metadata.get("page", "?")
                        location = f"第 {page} 页"

                    st.markdown(f"**{source}** · {location}")
                    st.caption(doc.page_content[:200] + "...")

    st.session_state.messages.append({"role": "assistant", "content": answer})