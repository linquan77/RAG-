import chromadb
from config import CHROMA_DB_PATH

def get_client():
    return chromadb.PersistentClient(path=CHROMA_DB_PATH)

def list_documents():
    """获取所有已入库的文档列表，按文件名去重"""
    try:
        client = get_client()
        collections = client.list_collections()
        if not collections:
            return []

        collection = client.get_collection(collections[0].name)
        result = collection.get(include=["metadatas"])

        # 按文件名去重，统计每个文件的切块数
        doc_map = {}
        for meta in result["metadatas"]:
            source = meta.get("source", "未知文件")
            # 只取文件名，不显示完整路径
            filename = source.split("/")[-1].split("\\")[-1]
            if filename not in doc_map:
                doc_map[filename] = {"source": source, "count": 0}
            doc_map[filename]["count"] += 1

        return [
            {"filename": k, "source": v["source"], "chunks": v["count"]}
            for k, v in doc_map.items()
        ]
    except Exception:
        return []

def delete_document(source_path: str):
    """删除指定文档的所有切块"""
    try:
        client = get_client()
        collections = client.list_collections()
        if not collections:
            return 0

        collection = client.get_collection(collections[0].name)

        # 查找该文件的所有切块 id
        result = collection.get(
            where={"source": source_path},
            include=["metadatas"]
        )
        ids = result["ids"]
        if ids:
            collection.delete(ids=ids)
        return len(ids)
    except Exception as e:
        raise e

def clear_all():
    """清空整个知识库"""
    try:
        client = get_client()
        for col in client.list_collections():
            client.delete_collection(col.name)
        return True
    except Exception:
        return False