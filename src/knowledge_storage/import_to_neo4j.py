import json
from neo4j import GraphDatabase

# --- 1. Neo4j 连接配置 ---
# 替换为您的远程 Neo4j 服务器信息
NEO4J_URI = "neo4j+ssc://a3d54e0b.databases.neo4j.io"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "17_Up5JUzf-iRepWtq_XP5QbrPe7HpbkXOLgPn-HSzY"

# --- 2. 节点文件和标签配置 ---
KG_ENTITY_DIR = "./data/KG/entity/"

NODE_FILES_CONFIG = [
    {
        "file_name": f"{KG_ENTITY_DIR}application.json",
        "label": "Application",
        "primary_key": "name"
    },
    {
        "file_name": f"{KG_ENTITY_DIR}concept.json",
        "label": "Concept",
        "primary_key": "name"
    },
    {
        "file_name": f"{KG_ENTITY_DIR}document.json",
        "label": "Document",
        "primary_key": "title"
    },
    {
        "file_name": f"{KG_ENTITY_DIR}technology.json",
        "label": "Technology",
        "primary_key": "name"
    }
]

# --- 3. 关系文件配置 ---
RELATION_FILE = "./data/KG/relationship/all_relations_fused.json"
BATCH_SIZE = 1000  # 每次向数据库提交的批处理大小


def create_constraints(driver, node_configs):
    """为每个节点标签的主键创建唯一性约束（使用现代 Cypher 语法）"""
    with driver.session() as session:
        for config in node_configs:
            label = config['label']
            pk = config['primary_key']

            # --- 语法已修复 ---
            # 使用 "FOR (n:Label) REQUIRE n.pk IS UNIQUE"
            query = f"CREATE CONSTRAINT IF NOT EXISTS FOR (n:{label}) REQUIRE n.{pk} IS UNIQUE"

            try:
                session.run(query)
                print(f"Constraint created for :{label}({pk})")
            except Exception as e:
                # 约束创建失败现在只会打印错误，但不会停止脚本
                print(f"Error creating constraint for :{label}({pk}): {e}")


def import_nodes(driver, config, batch_size):
    """
    导入单个JSON文件中的所有节点。
    会跳过主键 (pk) 为 null 的条目。
    """
    label = config['label']
    pk = config['primary_key']
    file_name = config['file_name']

    print(f"\nImporting nodes from {file_name} as :{label}...")

    # --- 查询已修复 ---
    # 1. WITH props -> 确保 props 在后续子句中可用
    # 2. WHERE props.{pk} IS NOT NULL -> 过滤掉主键为 null 的数据
    # 3. RETURN count(n) -> 返回实际合并/创建的节点数
    query = f"""
    UNWIND $batch as props
    WITH props
    WHERE props.{pk} IS NOT NULL
    MERGE (n:{label} {{{pk}: props.{pk}}})
    SET n = props
    RETURN count(n) as merged_count
    """

    try:
        with open(file_name, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"Error: File not found: {file_name}. Skipping...")
        return
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON from {file_name}. Skipping...")
        return

    with driver.session() as session:
        total_processed = 0
        total_merged = 0
        for i in range(0, len(data), batch_size):
            batch = data[i:i + batch_size]

            try:
                result = session.run(query, batch=batch)

                merged_count = result.single()["merged_count"]
                total_merged += merged_count
                total_processed += len(batch)

                skipped_count = len(batch) - merged_count

                print(f"  ... processed {total_processed}/{len(data)} nodes (merged {total_merged} total)")
                if skipped_count > 0:
                    print(f"      -> SKIPPED {skipped_count} nodes in this batch (null primary key: '{pk}')")

            except Exception as e:
                print(f"Error during batch import for {label}: {e}")
                print("Stopping import for this file.")
                break

    print(f"Finished importing :{label}. Total merged: {total_merged}, Total skipped: {len(data) - total_merged}")


def get_relationship_query(node_configs):
    """
    动态构建用于匹配关系中 subject 和 object 的 Cypher 查询。
    使用 APOC 来创建动态关系类型。
    """

    s_matches = []
    for cfg in node_configs:
        pk = cfg['primary_key']
        label = cfg['label']
        s_matches.append(f"OPTIONAL MATCH (s_{label.lower()}:{label} {{{pk}: row.subject}})")
    s_coalesce = ", ".join([f"s_{cfg['label'].lower()}" for cfg in node_configs])

    o_matches = []
    for cfg in node_configs:
        pk = cfg['primary_key']
        label = cfg['label']
        o_matches.append(f"OPTIONAL MATCH (o_{label.lower()}:{label} {{{pk}: row.object}})")
    o_coalesce = ", ".join([f"o_{cfg['label'].lower()}" for cfg in node_configs])

    # --- 查询已修改 ---
    query = f"""
    UNWIND $batch as row

    // 1. 查找 Subject (在所有节点类型中)
    {chr(10).join(s_matches)}
    WITH row, coalesce({s_coalesce}) AS s
    WHERE s IS NOT NULL

    // 2. 查找 Object (在所有节点类型中)
    {chr(10).join(o_matches)}
    WITH s, row, coalesce({o_coalesce}) AS o
    WHERE o IS NOT NULL

    // 3. 创建关系 (使用 APOC 实现动态类型)
    // 我们使用 apoc.merge.relationship 来代替 MERGE
    // apoc.merge.relationship(startNode, relationshipType, identProps, mergeProps, endNode)
    // row.relation 将被用作关系的 *标签* (类型)
    CALL apoc.merge.relationship(s, row.relation, {{}}, {{}}, o) YIELD rel

    RETURN count(rel) AS created_count
    """

    return query


def import_relationships(driver, node_configs, relation_file, batch_size):
    """导入关系"""
    print(f"\nImporting relationships from {relation_file}...")

    query = get_relationship_query(node_configs)

    try:
        with open(relation_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"Error: File not found: {relation_file}. Skipping.")
        return
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON from {relation_file}. Skipping.")
        return

    with driver.session() as session:
        total_created = 0
        total_processed = 0
        for i in range(0, len(data), batch_size):
            batch = data[i:i + batch_size]
            try:
                result = session.run(query, batch=batch)

                created_count = result.single()["created_count"]
                total_created += created_count
                total_processed += len(batch)
                print(f"  ... processed {total_processed}/{len(data)} relations (created {total_created} new)")

            except Exception as e:
                print(f"Error during relationship batch import: {e}")
                print("Stopping relationship import.")
                break

    print(f"Finished importing relationships. Total created: {total_created}")


def main():
    try:
        driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
        driver.verify_connectivity()
        print(f"Successfully connected to Neo4j at {NEO4J_URI}")
    except Exception as e:
        print(f"Failed to connect to Neo4j. Please check URI, USER, and PASSWORD.")
        print(f"Error: {e}")
        return

    try:
        # 1. 创建约束（重要！）
        create_constraints(driver, NODE_FILES_CONFIG)

        # 2. 导入所有节点
        for config in NODE_FILES_CONFIG:
            import_nodes(driver, config, BATCH_SIZE)

        # 3. 导入所有关系
        import_relationships(driver, NODE_FILES_CONFIG, RELATION_FILE, BATCH_SIZE)

        print("\n--- Import Complete! ---")

    finally:
        driver.close()
        print("Neo4j connection closed.")


if __name__ == "__main__":
    main()
