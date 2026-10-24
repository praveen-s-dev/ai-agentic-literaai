import streamlit as st

from app import setup_logging
from app.config import settings
from database.connection import check_db_connection
from database import init_db


def check_vector_db() -> tuple[bool, str]:
    from pathlib import Path
    vector_path = Path(settings.vector_db_path)
    if vector_path.exists():
        return True, f"Vector DB exists at {vector_path}"
    else:
        return False, f"Vector DB not initialized at {vector_path}"


def check_ollama() -> tuple[bool, str]:
    import httpx
    try:
        response = httpx.get(f"{settings.ollama_base_url}/api/tags", timeout=5.0)
        if response.status_code == 200:
            return True, f"Ollama reachable at {settings.ollama_base_url}"
        return False, f"Ollama returned status {response.status_code}"
    except Exception as e:
        return False, f"Ollama not reachable: {str(e)}"


def main():
    st.set_page_config(
        page_title="Research Assistant - Health Check",
        page_icon="🔬",
        layout="wide",
    )

    st.title("🔬 Evidence-Grounded Research Assistant")
    st.subheader("System Health & Status")

    st.divider()

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### Application Status")
        st.success("✅ Application Running")

        st.markdown("### Configuration")
        st.json({
            "LLM Provider": settings.llm_provider,
            "Ollama Base URL": settings.ollama_base_url,
            "Ollama Model": settings.ollama_model,
            "App Host": settings.app_host,
            "App Port": settings.app_port,
            "Log Level": settings.log_level,
        })

    with col2:
        st.markdown("### Database Status")
        db_healthy = check_db_connection()
        if db_healthy:
            st.success("✅ Database Connected")
        else:
            st.error("❌ Database Connection Failed")

        st.markdown("### Vector Database Status")
        vec_healthy, vec_msg = check_vector_db()
        if vec_healthy:
            st.success(f"✅ {vec_msg}")
        else:
            st.warning(f"⚠️ {vec_msg}")

        st.markdown("### Academic APIs")
        openalex_configured = bool(settings.openalex_api_key)
        semantic_scholar_configured = bool(settings.semantic_scholar_api_key)

        if openalex_configured:
            st.success("✅ OpenAlex API Key Configured")
        else:
            st.info("ℹ️ OpenAlex API Key Not Configured (optional)")

        if semantic_scholar_configured:
            st.success("✅ Semantic Scholar API Key Configured")
        else:
            st.info("ℹ️ Semantic Scholar API Key Not Configured (optional)")

    st.divider()

    st.markdown("### LLM Provider Status")
    ollama_healthy, ollama_msg = check_ollama()
    if ollama_healthy:
        st.success(f"✅ {ollama_msg}")
    else:
        st.error(f"❌ {ollama_msg}")
        st.info("Start Ollama with: `ollama serve`")

    st.divider()

    with st.expander("🔧 Initialize Database"):
        if st.button("Initialize Database Tables"):
            try:
                init_db()
                st.success("Database tables created successfully!")
            except Exception as e:
                st.error(f"Failed to initialize database: {e}")

    with st.expander("📋 Environment Variables"):
        st.code(f"""
LLM_PROVIDER={settings.llm_provider}
OLLAMA_BASE_URL={settings.ollama_base_url}
OLLAMA_MODEL={settings.ollama_model}
DATABASE_URL={settings.database_url}
VECTOR_DB_PATH={settings.vector_db_path}
APP_HOST={settings.app_host}
APP_PORT={settings.app_port}
LOG_LEVEL={settings.log_level}
OPENALEX_API_KEY={'***' if settings.openalex_api_key else 'Not set'}
SEMANTIC_SCHOLAR_API_KEY={'***' if settings.semantic_scholar_api_key else 'Not set'}
        """.strip())


if __name__ == "__main__":
    setup_logging()
    main()