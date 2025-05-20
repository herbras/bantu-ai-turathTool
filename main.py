import asyncio
import ssl
from os import getenv, path
import logging
import types
import uvicorn
import paramiko
from agno.tools.docker import DockerTools

from dotenv import load_dotenv
from agno.agent import Agent
from agno.models.openai.like import OpenAILike
from agno.playground import Playground
from agno.storage.sqlite import SqliteStorage
from agno.tools.mcp import MCPTools
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from agno.team import Team
from typing import List, Dict, Optional, Any, Callable

load_dotenv()

logging.basicConfig(
    level=getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

ssl._create_default_https_context = ssl._create_unverified_context

agent_storage: str = getenv("AGENT_STORAGE_DB", "tmp/agents.db")
mcp_server_url: str = getenv("MCP_SERVER_URL", "http://localhost:8001/sse")
openrouter_api_key: str | None = getenv(
    "OPENROUTER_API_KEY",
    "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",
)

if not openrouter_api_key:
    logger.error("OPENROUTER_API_KEY not found in environment variables.")
    raise ValueError("OPENROUTER_API_KEY is required.")

app = FastAPI()

# Add global middleware like CORS to the main app
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4321"],  # Consider making this configurable via environment variables
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Define the SSHDockerTools class
class SSHDockerTools(DockerTools):
    def __init__(
        self, host, username, password=None, key_filepath=None, **kwargs
    ):  # Added **kwargs
        self.host = host
        self.username = username
        self.password = password
        self.key_filepath = key_filepath
        self.ssh_client = None
        # Pass kwargs to DockerTools parent in case it uses them (e.g. enable_container_management)
        super().__init__(**kwargs)

    def connect(self):
        """Membuat koneksi SSH ke server remote."""
        self.ssh_client = paramiko.SSHClient()
        self.ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            if self.key_filepath:
                logger.info(
                    f"Connecting to {self.host}@{self.username} using key {self.key_filepath}"
                )
                self.ssh_client.connect(
                    self.host, username=self.username, key_filename=self.key_filepath
                )
            elif self.password:
                logger.info(f"Connecting to {self.host}@{self.username} using password")
                self.ssh_client.connect(
                    self.host, username=self.username, password=self.password
                )
            else:
                raise ValueError(
                    "SSH connection requires either a key_filepath or a password."
                )
            logger.info(f"Successfully connected to {self.host}")
        except Exception as e:
            logger.error(f"SSH connection to {self.host} failed: {e}")
            self.ssh_client = None  # Ensure client is None on failure
            raise  # Re-raise the exception to be caught by the agent/tool execution layer

    def execute(self, command):
        """Menjalankan perintah di server remote melalui SSH."""
        if not self.ssh_client:
            self.connect()
        if not self.ssh_client:  # Still no client after attempting connection
            return "SSH connection failed. Cannot execute command."

        logger.info(f"Executing command on {self.host}: {command}")
        stdin, stdout, stderr = self.ssh_client.exec_command(command)
        err = stderr.read().decode()
        if err:
            logger.error(f"SSH command error for '{command}': {err}")
            # Consider if error should be returned or raised. Returning for now.
            return f"Error executing command: {err}"
        return stdout.read().decode()

    def list_containers(self):
        """Menampilkan daftar kontainer yang berjalan di server remote."""
        return self.execute("docker ps")

    def list_images(self):
        """Menampilkan daftar gambar Docker di server remote."""
        return self.execute("docker images")

    def pull_image(self, image_name: str):
        """Menarik gambar Docker dari Docker Hub ke server remote."""
        return self.execute(f"docker pull {image_name}")

    def run_container(
        self, image_name: str, container_name: str, ports: str | None = None
    ):
        """Menjalankan kontainer Docker di server remote."""
        port_mapping = f"-p {ports}" if ports else ""
        return self.execute(
            f"docker run --name {container_name} {port_mapping} -d {image_name}"
        )

    def stop_container(self, container_name: str):
        """Menghentikan kontainer Docker di server remote."""
        return self.execute(f"docker stop {container_name}")

    def remove_container(self, container_name: str):
        """Menghapus kontainer Docker dari server remote."""
        return self.execute(f"docker rm {container_name}")

    def get_container_logs(self, container_name: str):
        """Retrieves logs from a container on the remote server."""
        return self.execute(f"docker logs {container_name}")

    def inspect_image(self, image_name: str):
        """Gets detailed information about an image on the remote server."""
        return self.execute(f"docker inspect {image_name}")

    def list_volumes(self):
        """Menampilkan daftar volume Docker di server remote."""
        return self.execute("docker volume ls")

    def create_network(self, network_name: str):
        """Membuat jaringan Docker di server remote."""
        return self.execute(f"docker network create {network_name}")

    def remove_network(self, network_name: str):
        """Menghapus jaringan Docker dari server remote."""
        return self.execute(f"docker network rm {network_name}")

    def __del__(self):
        if self.ssh_client:
            logger.info(f"Closing SSH connection to {self.host}")
            self.ssh_client.close()


class DynamicToolDiscovery:
    def __init__(self, mcp_server_url: str):
        """Initialize the DynamicToolDiscovery with MCP server URL."""
        self.mcp_server_url = mcp_server_url
        self.available_tools: Dict[str, Dict[str, Any]] = {}
        self.logger = logging.getLogger(__name__)
    
    async def initialize(self):
        """Initialize and discover all available tools from MCP server."""
        try:
            async with MCPTools(transport="sse", url=self.mcp_server_url) as mcp_tools:
                # Get all available tools from MCP server
                self.available_tools = await mcp_tools.list_available_tools()
                self.logger.info(f"Discovered {len(self.available_tools)} tools from MCP server")
                return self.available_tools
        except Exception as e:
            self.logger.error(f"Failed to initialize dynamic tool discovery: {e}")
            return {}
    
    async def get_relevant_tools(self, user_query: str, agent: Agent) -> List[Any]:
        """
        Find and return tools relevant to the user query that aren't already in the agent.
        
        Args:
            user_query: The user's input query
            agent: The agent that will use the tools
            
        Returns:
            List of tools relevant to the query
        """
        try:
            # Get currently configured tools in agent
            current_tool_names = {tool.__class__.__name__ for tool in agent.tools}
            
            # Connect to MCP server
            async with MCPTools(transport="sse", url=self.mcp_server_url) as mcp_tools:
                # Use the tool selection API to find relevant tools for the query
                relevant_tools = await mcp_tools.semantic_tool_search(
                    query=user_query,
                    max_results=5,
                    min_relevance_score=0.7
                )
                
                # Filter out tools that are already in the agent
                new_tools = []
                for tool_info in relevant_tools:
                    tool_name = tool_info["name"]
                    if tool_name not in current_tool_names:
                        # Initialize the tool from MCP server
                        tool = await mcp_tools.get_tool(tool_name)
                        if tool:
                            new_tools.append(tool)
                            self.logger.info(f"Dynamically added tool: {tool_name}")
                
                return new_tools
        except Exception as e:
            self.logger.error(f"Error finding relevant tools: {e}")
            return []

class DynamicAgent(Agent):
    """Agent that can dynamically discover and use tools based on user queries."""
    
    def __init__(self, *args, mcp_server_url: str = None, **kwargs):
        """Initialize DynamicAgent with tool discovery capabilities."""
        super().__init__(*args, **kwargs)
        self.tool_discovery = DynamicToolDiscovery(mcp_server_url) if mcp_server_url else None
        self.default_tools = self.tools.copy()
        self.tool_performance_cache = {}  # Track tool performance
    
    async def initialize(self):
        """Initialize the agent and discover available tools."""
        if self.tool_discovery:
            await self.tool_discovery.initialize()
    
    async def handle_query(self, query: str, **kwargs):
        """
        Handle user query with dynamic tool discovery.
        
        If default tools fail or perform poorly, automatically search for
        other relevant tools and retry the query.
        """
        # First attempt with default tools
        result = await super().handle_query(query, **kwargs)
        
        # Check if tool calls failed or performed poorly
        tool_failure = self._check_tool_failure(result)
        poor_performance = self._evaluate_performance(result, query)
        
        if tool_failure or poor_performance:
            self.logger.info("Default tools inadequate, searching for better tools...")
            
            # Get relevant tools for this query
            if self.tool_discovery:
                new_tools = await self.tool_discovery.get_relevant_tools(query, self)
                
                if new_tools:
                    # Add new tools to agent temporarily
                    original_tools = self.tools
                    self.tools = original_tools + new_tools
                    
                    # Retry the query with enhanced tools
                    enhanced_result = await super().handle_query(query, **kwargs)
                    
                    # Record performance of new tools
                    self._record_tool_performance(new_tools, enhanced_result, query)
                    
                    # Restore original tools
                    self.tools = original_tools
                    
                    # Keep high-performing tools for similar future queries
                    self._retain_valuable_tools(new_tools, query)
                    
                    return enhanced_result
            
        return result
    
    def _check_tool_failure(self, result) -> bool:
        """Check if any tool calls failed."""
        # Implementation will depend on how you detect tool failures
        # Example: check for error messages or specific patterns in result
        return "tool execution failed" in str(result).lower()
    
    def _evaluate_performance(self, result, query) -> bool:
        """Evaluate if tool performance was poor for this query."""
        # Implement your performance evaluation logic
        # Could be based on response time, accuracy, or other metrics
        return False  # Placeholder
    
    def _record_tool_performance(self, tools, result, query):
        """Record performance of tools for future reference."""
        for tool in tools:
            tool_name = tool.__class__.__name__
            # Implement your performance scoring mechanism
            self.tool_performance_cache[tool_name] = {
                "query_type": self._categorize_query(query),
                "performance_score": 0.8,  # Example score
                "last_used": "timestamp"
            }
    
    def _retain_valuable_tools(self, new_tools, query):
        """Keep high-performing tools for similar future queries."""
        query_category = self._categorize_query(query)
        for tool in new_tools:
            tool_name = tool.__class__.__name__
            if tool_name in self.tool_performance_cache:
                if self.tool_performance_cache[tool_name]["performance_score"] > 0.8:
                    if tool not in self.default_tools:
                        self.default_tools.append(tool)
                        self.logger.info(f"Permanently added high-performing tool: {tool_name}")
    
    def _categorize_query(self, query) -> str:
        """Categorize the query type for better tool matching."""
        # Implement query categorization logic
        # Could use keywords, NLP techniques, or embedding similarity
        return "general"  # Placeholder

async def create_configured_app() -> FastAPI:
    """
    Performs the core setup of agents and playground,
    returning the fully configured FastAPI app instance generated by the Playground.
    This instance's router will be included by the main app.
    """
    # SSH Docker Agent Setup
    # Use hardcoded SSH details as per user request
    ssh_host = "47.128.170.173"
    ssh_username = "ubuntu"
    ssh_key_filepath = path.expanduser("~/.ssh/agrego")  # Expand ~ to full path
    ssh_password = None  # Explicitly None as IdentityFile is used
    ssh_docker_management_team = None

    logger.info(
        f"Attempting to use SSH config: Host={ssh_host}, User={ssh_username}, IdentityFile={ssh_key_filepath}"
    )

    if ssh_host and ssh_username and (ssh_key_filepath or ssh_password):
        logger.info(
            f"Configuring SSH Docker Agent for host: {ssh_host}, user: {ssh_username}"
        )
        try:
            # Instantiate with default DockerTools params enabled, SSHDockerTools will override relevant methods
            ssh_docker_tools = SSHDockerTools(
                host=ssh_host,
                username=ssh_username,
                key_filepath=ssh_key_filepath,
                password=ssh_password,
                enable_container_management=True,  # from DockerTools
                enable_image_management=True,  # from DockerTools
                enable_volume_management=True,  # from DockerTools (default False, enabling)
                enable_network_management=True,  # from DockerTools (default False, enabling)
            )

            ssh_docker_agent = Agent(
                name="Docker Agent Remote",
                model=OpenAILike(
                    id="google/gemini-2.5-flash-preview:thinking",
                    api_key=openrouter_api_key,
                    base_url="https://openrouter.ai/api/v1",
                ),
                tools=[ssh_docker_tools],
                instructions=[
                    "You are an assistant for managing Docker on a remote server via SSH.",
                    "You can list, pull, run, stop, and remove Docker containers and images.",
                    "You can also manage Docker volumes and networks.",
                    "Use the provided tools to interact with Docker on the pre-configured remote server.",
                    "When the 'list_containers' tool is used, its output is the direct text result of the 'docker ps' command.",
                    "If this output contains lines with container information (typically includes headers like CONTAINER ID, IMAGE, COMMAND, CREATED, STATUS, PORTS, NAMES), you MUST report these details.",
                    "If the output is empty or only contains headers but no container lines, then you can state that no containers are running.",
                    "If a command fails, report the error message returned by the tool.",
                ],
                storage=SqliteStorage(
                    table_name="ssh_docker_agent", db_file=agent_storage
                ),
                add_datetime_to_instructions=True,
                add_history_to_messages=True,
                num_history_responses=3,
                markdown=True,
                reasoning=True,
                show_tool_calls=True,
            )

            ssh_docker_management_team = Team(
                name="SSH Docker Management Team",
                mode="coordinate",
                model=OpenAILike(
                    id="google/gemini-2.5-flash-preview:thinking",
                    api_key=openrouter_api_key,
                    base_url="https://openrouter.ai/api/v1",
                ),
                members=[ssh_docker_agent],
                description="Manages Docker resources (containers, images, volumes, networks) on a remote server via SSH.",
                instructions=[
                    "Receive user requests related to remote Docker management.",
                    "Delegate tasks to the 'Docker Agent Remote' to execute commands on the remote server via SSH.",
                    "Present results or error messages from the agent to the user.",
                ],
                add_datetime_to_instructions=True,
                enable_agentic_context=True,
                share_member_interactions=True,
                show_members_responses=True,
                markdown=True,
            )

            # Patch initialize_agent for the new team
            if hasattr(ssh_docker_management_team, "initialize_team") and not hasattr(
                ssh_docker_management_team, "initialize_agent"
            ):
                logger.info(
                    "Patching 'ssh_docker_management_team' instance: setting 'initialize_agent' to call 'initialize_team'."
                )

                def initialize_agent_for_team(self_instance, *args, **kwargs):
                    return self_instance.initialize_team(*args, **kwargs)

                ssh_docker_management_team.initialize_agent = types.MethodType(
                    initialize_agent_for_team, ssh_docker_management_team
                )
            elif not hasattr(ssh_docker_management_team, "initialize_agent"):
                logger.warning(
                    "Patching 'ssh_docker_management_team' instance: 'initialize_team' not found. Adding a no-op 'initialize_agent'."
                )

                def no_op_initialize_agent_method(self_instance, *args, **kwargs):
                    logger.info(
                        f"No-op initialize_agent called on {self_instance.name}"
                    )

                ssh_docker_management_team.initialize_agent = types.MethodType(
                    no_op_initialize_agent_method, ssh_docker_management_team
                )
            logger.info("SSH Docker Agent and Team configured successfully.")
        except Exception as e:
            logger.error(
                f"Failed to initialize SSH Docker Agent or Team: {e}", exc_info=True
            )
            ssh_docker_management_team = None  # Ensure it's None if setup fails
    else:
        logger.warning(
            "SSH Docker Agent not configured. Required environment variables "
            "(SSH_HOST, SSH_USERNAME, and SSH_KEY_FILEPATH or SSH_PASSWORD) are not all set. Skipping SSH Docker agent setup."
        )

    logger.info(f"Attempting to connect to MCP server at {mcp_server_url}...")
    async with MCPTools(transport="sse", url=mcp_server_url) as turath_mcp_tools:
        logger.info("Successfully connected to MCP server.")

        turath_query_agent_instructions = [
            "You are an expert on Islamic heritage and texts (Turath). Your primary language for interacting with tools is Arabic.",
            "Your answers MUST be strictly derived from the information provided by the tools. Do NOT add any information or make conclusions not directly supported by the tool's output.",
            "Your main task is to answer user questions by searching the Turath library.",
            "  1. Identify the main search topic and any potential filter criteria (like category names e.g., 'Fiqih', 'Mazhab Syafi'i', 'Aqidah', or author names) from the user's query.",
            "  2. Translate the main search topic into accurate Arabic. This will be the 'q' parameter for 'search_library'.",
            "  3. If filter criteria (category or author names) are identified:",
            "     a. Use the 'get_filter_ids' tool. Pass the identified category name to 'category_name' parameter and/or author name to 'author_name' parameter of the 'get_filter_ids' tool.",
            "     b. The 'get_filter_ids' tool will return a dictionary with 'category_ids' and/or 'author_ids'. These will be comma-separated strings of IDs.",
            "     c. Store these IDs to be used as 'cat' or 'author' parameters for the 'search_library' tool.",
            "  4. Call the 'search_library' tool: ",
            "     a. Use the translated Arabic topic as the 'q' parameter.",
            "     b. If you obtained 'category_ids' from 'get_filter_ids', use that string as the 'cat' parameter.",
            "     c. If you obtained 'author_ids' from 'get_filter_ids', use that string as the 'author' parameter.",
            "     d. Do not pass 'cat' or 'author' parameters if no IDs were found or if no filter criteria were identified.",
            "When processing results from 'search_library':",
            "  a. For each item within the 'data' array that you use to construct your answer, you MUST extract information primarily from its 'text' and/or 'snip' fields.",
            "  b. For every piece of information or summary derived from an item's 'text' or 'snip', you MUST immediately present its corresponding 'reference_info' field **in its entirety, including any provided links**. Format this as: 'Sumber: [full content of the reference_info field from that specific item]'.",
            "  c. If you synthesize information from multiple items for a single point in your answer, you must clearly cite all corresponding 'reference_info' (including links) for each part of the synthesis.",
            "  d. If the tool output includes a 'count' field indicating the total number of results, you may mention this if it'srelevant (e.g., 'Ditemukan X hasil, berikut adalah beberapa di antaranya:').",
            "Use other available tools like 'get_book_details' or 'get_page_content' as needed, always ensuring that conclusions are based on tool output and references are cited if applicable (e.g., from book metadata).",
            "Provide clear, concise, and informative answers.",
            "If providing book details or search results, format them clearly for the user, ensuring each piece of information is followed by its source.",
            "If a search yields no results or an error occurs, inform the user politely and state the query that was attempted (both original and translated, and any filters applied).",
        ]

        turath_query_agent = DynamicAgent(
            name="Turath Query Agent",
            model=OpenAILike(
                id="google/gemini-2.5-flash-preview:thinking",
                api_key=openrouter_api_key,
                base_url="https://openrouter.ai/api/v1",
            ),
            tools=[turath_mcp_tools],
            mcp_server_url=mcp_server_url,
            instructions=turath_query_agent_instructions,
            storage=SqliteStorage(
                table_name="turath_query_agent", db_file=agent_storage
            ),
            add_datetime_to_instructions=True,
            add_history_to_messages=True,
            num_history_responses=3,
            markdown=True,
            reasoning=True,
            show_tool_calls=True,
        )

        # Initialize the dynamic tool discovery
        await turath_query_agent.initialize()

        # Agent 2: TurathArticleWriterAgent (for writing articles)
        turath_article_writer_instructions = [
            "You are an expert on Islamic heritage and texts (Turath), specialized in writing articles. Your primary language for interacting with tools is Arabic.",
            "Your answers MUST be strictly derived from the information provided by the tools. Do NOT add any information or make conclusions not directly supported by the tool's output. All claims and theoretical foundations in the article MUST be backed by data obtained from tool calls, and each such piece of information must be cited with its 'reference_info'.",
            "Your main task is to write articles based on user requests and information from the Turath library.",
            "If the user's request explicitly involves writing an article, composing content, or generating a piece of writing:",
            "  1. First, check if the user has already clearly specified ALL of the following in their initial request or recent conversation history:",
            "     - Persona Tulisan: The desired writing style, tone, and viewpoint (e.g., santai dan mudah dipahami, formal akademis, seperti Ustadz tertentu, semangat dakwah, dll.).",
            "     - Tujuan Dakwah: The primary message, impact, or goal the article aims to achieve (e.g., mengedukasi pemuda tentang tauhid, memperkuat aqidah Ahlus Sunnah wal Jama'ah, menjelaskan fiqih ibadah tertentu, membantah syubhat).",
            "     - Referensi Khusus: Specific books, authors, or topics from the Turath library to be used as primary sources (e.g., 'Kitab Al-Umm oleh Imam Syafi'i', 'tafsir ayat X dari Tafsir Ibnu Katsir', 'hadis tentang Birrul Walidain dari Sahih Bukhari').",
            "  2. If ALL THREE aspects (Persona, Tujuan, dan Referensi Khusus) are NOT YET CLEARLY SPECIFIED, then **DO NOT** attempt to generate the article yet. Instead, you MUST ask the user to provide all three in a single, polite turn:",
            '     "Untuk membantu saya menulis artikel yang paling sesuai, mohon informasikan:"',
            '     "  1. Persona atau gaya tulisan seperti apa yang Anda inginkan untuk artikel ini (misalnya, santai, formal, akademis, atau gaya penceramah tertentu)?"',
            '     "  2. Apa tujuan dakwah utama atau pesan inti yang ingin Anda sampaikan melalui artikel ini?"',
            "     \"  3. Adakah kitab, penulis, atau topik sumber spesifik dari Perpustakaan Turath yang Anda ingin saya jadikan rujukan utama? Jika Anda tidak yakin, sebutkan saja topik umumnya (misalnya 'qawaid fiqh mazhab Hanbali') dan saya akan coba carikan referensi yang relevan.\"",
            "     Wait for the user's complete answers to these three points before proceeding.",
            "  3. Once the user provides the Persona, Tujuan, and Referensi Khusus (or indicates to search for references):",
            "     a. For the 'Referensi Khusus':",
            "        i.   If the user provided a specific book name, author name, or topic (e.g., 'Kitab Al-Umm', 'Imam Syafi'i', 'qawaid fiqh Hanbali'), or if they answered 'terserah' or similar for references, you MUST treat this as a search query for the 'search_library' tool.",
            "        ii.  Identify the main search topic from the user's input for 'Referensi Khusus'. If the user said 'terserah' but mentioned a general article topic earlier (e.g., 'qawaid fikih mazhab hanbali'), use that general topic as the search query for references.",
            "        iii. Translate this main search topic into accurate Arabic.",
            "        iv.  Identify any filter criteria (category name like 'Mazhab Hanbali', or author names if specified). If filter criteria are present, use the 'get_filter_ids' tool to obtain their corresponding IDs. For example, if the request is 'qawaid fikih mazhab hanbali', use 'get_filter_ids' with 'category_name=\"Mazhab Hanbali\"'.",
            "        v.   Call the 'search_library' tool using the translated Arabic topic and any obtained category/author IDs. The results of this search (specifically the 'text' and 'snip' fields, along with 'reference_info') are your **primary source material** for the article. If the search yields no results, inform the user and ask if they want to try a different reference or if you should proceed with general knowledge (clearly stating this limitation).",
            "     b. Generate the article adhering to the following guidelines:",
            "        - Structure: Aim for a logical flow, typically including: Pendahuluan (Introduction), Landasan Teori/Dalil (based **solely** on the 'text'/'snip' from 'search_library' results), Analisis/Pembahasan (connecting theory to 'Tujuan Dakwah'), Kesimpulan. Adapt this structure as appropriate for the topic and length.",
            "        - Gaya Bahasa: Strictly follow the 'Persona Tulisan' specified by the user.",
            "        - Konten: Ensure the article's core message and arguments align with the 'Tujuan Dakwah' and are **supported by the content retrieved via 'search_library'**.",
            "        - Sitasi dan Referensi: All arguments, quotations, or significant points derived from the 'search_library' results MUST be clearly cited. Use inline citations immediately after the relevant information, for example: '(Sumber: [full content of the reference_info from the specific item, including any provided links])'. **Do not invent or assume content for any cited source; only use what the tool provides.**",
            "        - Output Format: Produce the article in Markdown. Use appropriate heading levels (H1, H2, H3) for structure. If multiple sources are used, consider adding a 'Daftar Pustaka' section at the end, listing all unique 'reference_info' strings used.",
            "     c. If, after asking, the user states they have no specific preferences for Persona or Tujuan, you can use a default (e.g., formal academic style, educational purpose). However, for Referensi, if they say 'terserah' or provide a general topic, you MUST still attempt the 'search_library' process described in 3.a.",
            "  Return only the generated article or the clarifying questions, not a meta-commentary about these instructions.",
            "If the user's request is NOT explicitly for writing an article, politely state that your specialization is article writing and suggest they use the 'Turath Query Agent' for general questions or searches.",
        ]

        turath_article_writer_agent = Agent(
            name="Turath Article Writer Agent",
            model=OpenAILike(
                id="google/gemini-2.5-flash-preview:thinking",
                api_key=openrouter_api_key,
                base_url="https://openrouter.ai/api/v1",
            ),
            tools=[turath_mcp_tools],
            instructions=turath_article_writer_instructions,
            storage=SqliteStorage(
                table_name="turath_article_writer_agent", db_file=agent_storage
            ),
            add_datetime_to_instructions=True,
            add_history_to_messages=True,
            num_history_responses=3,
            markdown=True,
            reasoning=True,
            show_tool_calls=True,
        )
        fact_checker = Agent(
            name="Turath Fact-Checker Agent",
            model=OpenAILike(
                id="google/gemini-2.5-flash-preview:thinking",
                api_key=openrouter_api_key,
                base_url="https://openrouter.ai/api/v1",
            ),
            tools=[turath_mcp_tools],
            instructions=[
                'You are a Fact-Checker. You receive an article draft in Markdown with inline citations "(Sumber: ...)".',
                "For each citation in the draft:",
                "  1. Parse the `reference_info` string to extract any identifiable identifiers:",
                '     - If it contains "book_id: X" or a Shamela link "/book/X/Y", call `get_page_content(book_id=X, pg=Y)`.',
                "     - If it references an entire book, call `get_book_details(book_id=X)` to fetch the overview and verify the title/author.",
                "     - Otherwise, treat the snippet text in the citation as a search query: translate back to Arabic if needed and call `search_library(q=that_snip)` to find the original context.",
                "  2. Compare the returned text from the tool with the drafted quotation/snippet:",
                "     - Confirm that the words and meaning match exactly (no insertion or omission).",
                "     - If there's a discrepancy, flag it and show:\"Citation mismatch: expected '...', but source says '... (Sumber: ...tool output...)'\".",
                '  3. If the tool call returns no data or an error, flag:"Could not verify citation for (Sumber: ...); source not found."',
                "After processing all citations, return a report listing:",
                "  - ✅ All verified citations",
                "  - ⚠️ Any mismatches or missing sources with details",
                "Do NOT invent any data—only use what the tools return.",
            ],
            reasoning=True,
            markdown=True,
            show_tool_calls=True,
        )

        turath_editor = Team(
            name="Turath Content Coordinator",
            mode="coordinate",
            model=OpenAILike(
                id="google/gemini-2.5-flash-preview:thinking",
                api_key=openrouter_api_key,
                base_url="https://openrouter.ai/api/v1",
            ),
            members=[
                turath_query_agent,
                turath_article_writer_agent,
                fact_checker,
            ],
            description=(
                "You are the Team Leader coordinating the production of high-quality Islamic articles.  "
                "First break down the user's request into search, drafting, and fact-checking tasks.  "
                "Then synthesize all member outputs into one coherent, fully-sourced final article."
            ),
            instructions=[
                "1. Terima permintaan user. Tentukan apakah ini soal pencarian atau penulisan artikel.",
                "2. Jika butuh referensi, delegasikan ke Turath Query Agent untuk `search_library` dan `get_filter_ids`.",
                "3. Terima hasil pencarian, terus berikan ke Turath Article Writer Agent untuk menghasilkan draf artikel.",
                "4. (Opsional) Berikan draf tersebut ke Turath Fact-Checker Agent untuk verifikasi sitasi.",
                "5. Ambil semua output, edit dan satukan menjadi satu artikel final Markdown:",
                "   - Pastikan setiap klaim memiliki sitasi 'Sumber: ...' sesuai `reference_info`.",
                "   - Periksa konsistensi persona dan tujuan dakwah.",
                "   - Tampilkan 'Daftar Pustaka' unik di akhir.",
                "Return only the final synthesized article.",
            ],
            add_datetime_to_instructions=True,
            enable_agentic_context=True,
            share_member_interactions=True,
            show_members_responses=True,
            markdown=True,
        )

        if hasattr(turath_editor, "initialize_team") and not hasattr(
            turath_editor, "initialize_agent"
        ):
            logger.info(
                "Patching 'turath_editor' instance: setting 'initialize_agent' to call 'initialize_team'."
            )

            def initialize_agent_for_team(self_instance, *args, **kwargs):
                return self_instance.initialize_team(*args, **kwargs)

            turath_editor.initialize_agent = types.MethodType(
                initialize_agent_for_team, turath_editor
            )
        elif not hasattr(turath_editor, "initialize_agent"):
            logger.warning(
                "Patching 'turath_editor' instance: 'initialize_team' not found. Adding a no-op 'initialize_agent'."
            )

            def no_op_initialize_agent_method(self_instance, *args, **kwargs):
                logger.info(f"No-op initialize_agent called on {self_instance.name}")

            turath_editor.initialize_agent = types.MethodType(
                no_op_initialize_agent_method, turath_editor
            )

        teams_for_playground = [turath_editor]
        if ssh_docker_management_team:
            teams_for_playground.append(ssh_docker_management_team)

        playground = Playground(teams=teams_for_playground,agents=[turath_query_agent, turath_article_writer_agent,ssh_docker_agent])

        final_app_instance = playground.get_app()

        @final_app_instance.get("/health_playground")  # Renamed path to avoid collision
        async def health_check_playground(): # Function name can be more descriptive
            return {"status": "ok", "source": "playground_app"}

        # IMPORTANT: CORSMiddleware is now handled by the global 'app' instance.
        # Do NOT add it here to final_app_instance.
        # REMOVE THE FOLLOWING BLOCK if it exists from previous versions:
        # final_app_instance.add_middleware(
        # CORSMiddleware,
        # allow_origins=["http://localhost:4321"],
        # allow_credentials=True,
        # allow_methods=["*"],
        # allow_headers=["*"],
        # )
        logger.info("FastAPI app instance from Playground has been configured and will be returned.")
        return final_app_instance


@app.on_event("startup")
async def on_startup_event(): # Renamed to avoid potential conflict if 'on_startup' is used as a variable
    """
    Saat server FastAPI mulai, bangun Playground-nya
    dan tambahkan routernya ke `app` utama.
    """
    logger.info("FastAPI startup event triggered. Configuring application...")
    playground_specific_app: FastAPI = await create_configured_app()

    # Salin semua route dari playground_specific_app ke app utama menggunakan include_router
    app.include_router(playground_specific_app.router)
    # If you want all playground routes to be prefixed, you can do it here:
    # app.include_router(playground_specific_app.router, prefix="/playground")

    logger.info("Playground routes have been included in the main FastAPI app.")


@app.get("/health") # This is the main application's health check
async def main_health_check():
    return {"status": "ok", "source": "main_app"}


if __name__ == "__main__":
    logger.info("Starting FastAPI server with Uvicorn (reload enabled)…")
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
