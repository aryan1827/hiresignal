"""The HireSignal skill taxonomy.

Each entry is ``(canonical name, category, patterns, options)``.

Pattern conventions
-------------------
* a plain phrase such as ``"machine learning"`` is matched case-insensitively
  as a whole word; spaces also match a hyphen ("machine-learning");
* ``"re:<regex>"`` is a raw case-insensitive regular expression;
* ``"cs:<regex>"`` is a raw case-sensitive regular expression, used for short
  names that are also ordinary English words (Go, R, C, Swift, Julia).

Options
-------
* ``exclude``: a regex checked on the 30 characters around a match; if it
  matches, that occurrence is ignored (e.g. "Series C" is not the C language);
* ``context``: the skill only counts when the posting also mentions at least
  two other skills, which filters out stray capitalised words.

Skills are counted on explicit mentions only. We do not infer that a Django
posting needs Python, because inferred pairs would make the association rules
report relationships we put there ourselves.
"""

T = []


def add(category, *entries):
    for e in entries:
        name, patterns, *rest = e
        T.append((name, category, patterns, rest[0] if rest else {}))


# ----------------------------------------------------------------- languages
add("Programming Languages",
    ("Python", ["python"]),
    ("JavaScript", ["javascript", "ecmascript", r"re:(?<![\w.])js(?![\w.])"]),
    ("TypeScript", ["typescript"]),
    ("Java", [r"re:\bjava\b(?![\s\-]?script)"], {"exclude": r"(?i)java\s?(?:island|coffee)"}),
    ("C++", [r"re:(?<![\w+])c\+\+(?![\w+])", r"\bcpp\b"]),
    ("C#", [r"re:(?<![\w#])c#(?!\w)", r"re:\bc\s?sharp\b"]),
    ("C", [r"cs:(?<![\w+#./\-])C(?![\w+#\-/]|\s?\+\+|\s?#|\.)"],
     {"exclude": r"(?i)(series|type|class|grade|level|vitamin|round|section|plan|tier|corp|suite|"
                 r"[a-z]\s?,\s?b\s?,\s?c|a/b/c|\bc\s?(?:level|suite|corp|round)|"
                 r"[$€£]\s?C|\bC\s?\$|°\s?C)", "context": True}),
    ("Go", ["golang", r"cs:\bGo\b(?![\s\-]?(?:to|live|ahead|getter|beyond|further|above|back|"
                      r"deep|out|on|over|through|for|with|into|from|fast|big|far|home|"
                      r"get|find|after|-to|-live|!))"],
     {"exclude": r"(?i)(let'?s go|ready to go|on the go|to go\b|go-to|go to market|"
                 r"pokemon go|\bgo\s+(?:the|a|an|our|your|their|and|is|are)\b)", "context": True}),
    ("Rust", [r"re:\brust\b(?![\s\-]?belt)"]),
    ("Ruby", ["ruby"]),
    ("PHP", ["php"]),
    ("Kotlin", ["kotlin"]),
    ("Swift", [r"cs:\bSwift\b(?!UI)"], {"exclude": r"(?i)(swift(?:ly)? (?:response|action|pace)|"
                                                    r"taylor swift|swift code|swift transfer)"}),
    ("Scala", ["scala"]),
    ("Elixir", ["elixir"]),
    ("Erlang", ["erlang"]),
    ("Haskell", ["haskell"]),
    ("Clojure", ["clojure", "clojurescript"]),
    ("OCaml", ["ocaml"]),
    ("F#", [r"re:(?<![\w#])f#(?!\w)"]),
    ("R", [r"cs:(?<![\w&/.\-'’])R(?![\w&'’.\-]|\s?&|\s?\+)"],
     {"exclude": r"(R\s?&\s?D|R\s?and\s?D|\(R\)|®|Series R|R\s?[0-9])", "context": True}),
    ("Julia", [r"cs:\bJulia\b"], {"context": True}),
    ("Perl", ["perl"]),
    ("Lua", ["lua"]),
    ("Dart", ["dart"]),
    ("Zig", [r"cs:\bZig\b"]),
    ("Solidity", ["solidity"]),
    ("Objective-C", [r"re:\bobjective[\s\-]?c\b", r"re:\bobjc\b"]),
    ("Bash/Shell", ["bash", "shell scripting", "shell scripts", r"re:\bzsh\b"]),
    ("PowerShell", ["powershell"]),
    ("SQL", [r"re:(?<![\w\-])sql(?!\w)"]),
    ("Fortran", ["fortran"]),
    ("COBOL", ["cobol"]),
    ("Groovy", ["groovy"]),
)

# ------------------------------------------------------------ frontend & web
add("Frontend & Web",
    ("React", [r"re:\breact(?:\.?js)?\b(?![\s\-]?native)"]),
    ("Angular", [r"re:\bangular(?:\.?js)?\b"]),
    ("Vue.js", [r"re:\bvue(?:\.?js)?\b"]),
    ("Svelte", [r"re:\bsvelte(?:kit)?\b"]),
    ("Next.js", [r"re:\bnext\.?js\b"]),
    ("Nuxt", [r"re:\bnuxt(?:\.?js)?\b"]),
    ("Redux", ["redux"]),
    ("HTML", [r"re:\bhtml5?\b"]),
    ("CSS", [r"re:\bcss3?\b"]),
    ("Tailwind CSS", ["tailwind"]),
    ("Sass", [r"re:\bsass\b|\bscss\b"]),
    ("jQuery", ["jquery"]),
    ("Webpack", ["webpack"]),
    ("Vite", [r"cs:\bVite\b"]),
    ("D3.js", [r"re:\bd3(?:\.js)?\b"]),
    ("Three.js", [r"re:\bthree\.?js\b"]),
    ("WebAssembly", ["webassembly", r"re:\bwasm\b"]),
    ("WebGL", ["webgl", "webgpu"]),
    ("Storybook", ["storybook"]),
    ("Accessibility", ["accessibility", r"re:\bwcag\b", r"re:\ba11y\b"]),
)

# --------------------------------------------------------- backend frameworks
add("Backend & APIs",
    ("Node.js", [r"re:\bnode\.?js\b", r"cs:\bNode\b(?!\s?(?:of|in))"]),
    ("Express", [r"re:\bexpress\.?js\b", r"re:\bexpressjs\b"]),
    ("NestJS", [r"re:\bnest\.?js\b"]),
    ("Django", ["django"]),
    ("Flask", [r"cs:\bFlask\b"]),
    ("FastAPI", ["fastapi"]),
    ("Spring Boot", [r"re:\bspring[\s\-]?boot\b", r"re:\bspring (?:framework|mvc|cloud|security)\b"]),
    (".NET", [r"re:(?<!\w)\.net\b(?!\w)", r"re:\bdotnet\b", r"re:\basp\.net\b"],
     {"exclude": r"(?i)\w\.net\b"}),
    ("Ruby on Rails", [r"re:\bruby on rails\b", r"re:\brails\b", r"cs:\bRoR\b"]),
    ("Laravel", ["laravel"]),
    ("Symfony", ["symfony"]),
    ("Phoenix", [r"cs:\bPhoenix\b(?=.{0,80}(?:Elixir|LiveView))", r"re:\bliveview\b"]),
    ("GraphQL", ["graphql"]),
    ("REST APIs", [r"re:\brestful\b", r"re:\brest[\s\-]?apis?\b", r"re:\brest\b(?=\s*(?:/|and|,|or)\s*graphql)"]),
    ("gRPC", ["grpc", "protobuf", "protocol buffers"]),
    ("Microservices", [r"re:\bmicro[\s\-]?services?\b"]),
    ("WebSockets", [r"re:\bweb[\s\-]?sockets?\b"]),
    ("RabbitMQ", ["rabbitmq"]),
    ("Celery", [r"cs:\bCelery\b"]),
    ("Hibernate", ["hibernate"]),
)

# -------------------------------------------------------- databases & storage
add("Databases",
    ("PostgreSQL", [r"re:\bpostgres(?:ql)?\b", r"re:\bpostgis\b"]),
    ("MySQL", ["mysql", "mariadb"]),
    ("SQLite", ["sqlite"]),
    ("SQL Server", [r"re:\bsql server\b", r"re:\bmssql\b", r"re:\bt-sql\b"]),
    ("Oracle DB", [r"re:\boracle (?:db|database|sql|pl/sql)\b", r"re:\bpl/sql\b"]),
    ("MongoDB", [r"re:\bmongo(?:db)?\b"]),
    ("Redis", ["redis"]),
    ("Elasticsearch", ["elasticsearch", "elastic search", "opensearch"]),
    ("Cassandra", [r"re:\bcassandra\b", "scylladb"]),
    ("DynamoDB", ["dynamodb"]),
    ("ClickHouse", ["clickhouse"]),
    ("Neo4j", ["neo4j"]),
    ("Supabase", ["supabase"]),
    ("Firebase", ["firebase", "firestore"]),
    ("CockroachDB", ["cockroachdb"]),
    ("NoSQL", ["nosql"]),
)

# ------------------------------------------------------------ cloud platforms
add("Cloud",
    ("AWS", [r"re:\baws\b", "amazon web services", r"re:\bec2\b", r"re:\bs3\b"]),
    ("GCP", [r"re:\bgcp\b", "google cloud"]),
    ("Azure", [r"re:\bazure\b"]),
    ("Serverless", ["serverless", "aws lambda", "cloud functions"]),
    ("Cloudflare", ["cloudflare"]),
    ("Vercel", ["vercel"]),
    ("Heroku", ["heroku"]),
    ("DigitalOcean", ["digitalocean", "digital ocean"]),
)

# --------------------------------------------------- devops & infrastructure
add("DevOps & Infrastructure",
    ("Docker", ["docker", "containerization", "containerisation"]),
    ("Kubernetes", ["kubernetes", r"re:\bk8s\b", r"re:\beks\b", r"re:\bgke\b", r"re:\baks\b"]),
    ("Terraform", ["terraform", "opentofu"]),
    ("Ansible", ["ansible"]),
    ("Helm", [r"cs:\bHelm\b"]),
    ("CI/CD", [r"re:\bci\s?/\s?cd\b", r"re:\bcicd\b", "continuous integration",
               "continuous delivery", "continuous deployment"]),
    ("GitHub Actions", ["github actions"]),
    ("Jenkins", ["jenkins"]),
    ("GitLab CI", [r"re:\bgitlab[\s\-]?ci\b"]),
    ("Argo CD", [r"re:\bargo\s?cd\b", r"re:\bargo workflows\b"]),
    ("Prometheus", ["prometheus"]),
    ("Grafana", ["grafana"]),
    ("Datadog", ["datadog"]),
    ("Observability", ["observability", "opentelemetry"]),
    ("Linux", [r"re:\blinux\b(?![\s\-]?kernel)"]),
    ("Nginx", ["nginx"]),
    ("Pulumi", ["pulumi"]),
    ("Infrastructure as Code", [r"re:\binfrastructure[\s\-]as[\s\-]code\b", r"cs:\bIaC\b"]),
    ("DevOps practices", [r"re:\bdevops\b"]),
)

# --------------------------------------------------------- data engineering
add("Data Engineering",
    ("Apache Spark", [r"re:\bapache spark\b", "pyspark", r"cs:\bSpark\b"],
     {"exclude": r"Spark\s+(?:Capital|Human|Joy|AR|Networks|Ventures|Labs)|to Spark", "context": True}),
    ("Kafka", ["kafka"]),
    ("Airflow", ["airflow"]),
    ("dbt", [r"re:\bdbt\b"]),
    ("Snowflake", [r"cs:\bSnowflake\b"], {"exclude": r"Snowflake(?:'s)?\s+(?:CEO|CTO|founder|alum|Inc|IPO)|(?:ex-|former\s)Snowflake"}),
    ("BigQuery", ["bigquery"]),
    ("Redshift", ["redshift"]),
    ("Databricks", ["databricks"]),
    ("Hadoop", ["hadoop", r"re:\bhive\b(?=.{0,40}(?:hadoop|sql|spark))"]),
    ("Flink", [r"re:\b(?:apache )?flink\b"]),
    ("ETL/ELT", [r"re:\betl\b", r"re:\belt pipelines?\b"]),
    ("Data warehousing", [r"re:\bdata[\s\-]?warehous\w*", "lakehouse", r"re:\bdata lakes?\b"]),
    ("Data pipelines", [r"re:\bdata pipelines?\b"]),
)

# --------------------------------------------------- data science & classic ML
add("Data Science & ML",
    ("Machine Learning", ["machine learning", r"cs:\bML\b"]),
    ("Deep Learning", ["deep learning", "neural networks", "neural network"]),
    ("PyTorch", ["pytorch", r"re:\btorch\b"]),
    ("TensorFlow", ["tensorflow"]),
    ("scikit-learn", [r"re:\bscikit[\s\-]?learn\b", "sklearn"]),
    ("Keras", ["keras"]),
    ("XGBoost", ["xgboost", "lightgbm", "catboost"]),
    ("Pandas", [r"cs:\b[Pp]andas\b"]),
    ("NumPy", ["numpy", "scipy"]),
    ("Jupyter", ["jupyter"]),
    ("Statistics", [r"re:\bstatistic(?:s|al)\b"]),
    ("NLP", [r"re:\bnlp\b", "natural language processing"]),
    ("Computer Vision", ["computer vision", r"re:\bimage (?:recognition|segmentation)\b"]),
    ("OpenCV", ["opencv"]),
    ("MLOps", ["mlops", "kubeflow", "mlflow", "sagemaker", "vertex ai"]),
    ("Recommender systems", [r"re:\brecommend(?:er|ation) (?:systems?|engines?)\b"]),
    ("Time series", [r"re:\btime[\s\-]series\b", "forecasting"]),
    ("A/B testing", [r"re:\ba/b test\w*", "experimentation platform"]),
    ("Reinforcement learning", ["reinforcement learning", r"re:\brlhf\b"]),
    ("CUDA/GPU", [r"re:\bcuda\b", r"re:\bgpu programming\b", r"re:\btriton\b(?=.{0,40}(?:kernel|gpu))"]),
    ("Tableau", ["tableau"]),
    ("Power BI", [r"re:\bpower\s?bi\b"]),
    ("Looker", ["looker"]),
    ("Excel", [r"cs:\bExcel\b(?!lent|lence)", r"re:\b(?:ms|microsoft|advanced) excel\b", r"re:\bspreadsheets?\b"]),
    ("Data visualization", [r"re:\bdata visuali[sz]ation\b", r"re:\bdashboards?\b"]),
    ("Data analysis", [r"re:\bdata analy(?:sis|tics)\b"]),
)

# --------------------------------------------------------- generative AI & LLMs
add("Generative AI & LLMs",
    ("LLMs", [r"re:\bllms?\b", r"re:\blarge language models?\b"]),
    ("Generative AI", [r"re:\bgenerative ai\b", r"re:\bgen\s?ai\b"]),
    ("RAG", [r"cs:\bRAG\b", r"re:\bretrieval[\s\-]augmented\b"]),
    ("LangChain", ["langchain", "langgraph"]),
    ("LlamaIndex", ["llamaindex", "llama index"]),
    ("Prompt engineering", [r"re:\bprompt (?:engineering|design)\b"]),
    ("Fine-tuning", [r"re:\bfine[\s\-]?tun\w+", r"cs:\bLoRA\b", r"re:\bpeft\b"]),
    ("OpenAI/GPT", ["openai", r"re:\bgpt-?\d", "chatgpt"]),
    ("Anthropic/Claude", ["anthropic", r"cs:\bClaude\b"]),
    ("Hugging Face", [r"re:\bhugging\s?face\b"]),
    ("Vector databases", [r"re:\bvector (?:database|db|store|search)s?\b", "pinecone", "weaviate",
                          "qdrant", "milvus", r"re:\bchroma(?:db)?\b", "pgvector"]),
    ("AI agents", [r"re:\bai agents?\b", "agentic", r"re:\bmulti[\s\-]agent\b",
                   r"re:\bautonomous agents?\b", r"re:\bllm agents?\b"]),
    ("Embeddings", [r"re:\bembeddings\b"]),
    ("MCP", [r"re:\bmodel context protocol\b", r"cs:\bMCP\b"], {"context": True}),
    ("LLM evals", [r"re:\bevals\b", r"re:\bllm evaluation\b", r"re:\bmodel evaluation\b"]),
    ("Diffusion models", [r"re:\bdiffusion models?\b", "stable diffusion"]),
    ("LLM inference", [r"re:\bvllm\b", r"re:\binference (?:optimi[sz]ation|serving|engine)\b",
                       r"re:\bllm inference\b"]),
)

# ------------------------------------------------------------------- mobile
add("Mobile",
    ("iOS", [r"cs:\biOS\b", r"re:\bios (?:developer|engineer|app)"]),
    ("Android", ["android"]),
    ("SwiftUI", ["swiftui"]),
    ("Flutter", ["flutter"]),
    ("React Native", [r"re:\breact[\s\-]native\b"]),
    ("Jetpack Compose", [r"re:\bjetpack compose\b"]),
    ("Xamarin/MAUI", ["xamarin", r"re:\b\.net maui\b"]),
)

# ----------------------------------------- embedded, hardware and telecom (EXTC)
add("Embedded, Hardware & Telecom",
    ("Embedded systems", [r"re:\bembedded (?:systems?|software|engineer\w*|development|devices?|c|c\+\+)\b",
                          r"re:\bembedded\b(?=.{0,30}(?:firmware|hardware|linux|rtos))"]),
    ("Firmware", ["firmware"]),
    ("RTOS", [r"re:\brtos\b", "freertos", r"re:\bzephyr\b", r"re:\breal[\s\-]time operating"]),
    ("Embedded Linux", [r"re:\bembedded linux\b", "yocto", "buildroot"]),
    ("Microcontrollers", [r"re:\bmicro[\s\-]?controllers?\b", r"re:\bmcus?\b", "stm32", "esp32",
                          "arduino", r"re:\barm cortex", r"re:\bnrf52\b"]),
    ("FPGA", ["fpga", r"re:\bxilinx\b", r"re:\bvivado\b"]),
    ("Verilog/SystemVerilog", ["verilog", "systemverilog", r"re:\buvm\b"]),
    ("VHDL", ["vhdl"]),
    ("ASIC design", [r"re:\basics?\b", r"re:\brtl design\b", r"re:\bphysical design\b"]),
    ("PCB design", [r"re:\bpcbs?\b", "altium", "kicad", r"re:\bschematic capture\b"]),
    ("Signal processing", [r"re:\bsignal processing\b", r"re:\bdsp\b"]),
    ("RF engineering", [r"re:\brf\b(?!\s?id)", r"re:\bradio frequency\b", r"re:\bantennas?\b"]),
    ("Wireless (BLE/Wi-Fi)", [r"re:\bbluetooth\b", r"re:\bble\b", r"re:\bwi[\s\-]?fi\b", "zigbee",
                              r"re:\blora(?:wan)?\b"]),
    ("5G/LTE", [r"re:\b5g\b", r"re:\blte\b", r"re:\bo-?ran\b", r"re:\b3gpp\b"]),
    ("IoT", [r"re:\biot\b", r"re:\binternet of things\b"]),
    ("MQTT", ["mqtt"]),
    ("CAN bus/AUTOSAR", [r"re:\bcan[\s\-]?bus\b", r"re:\bcan fd\b", "autosar"]),
    ("I2C/SPI/UART", [r"re:\bi2c\b", r"cs:\bSPI\b", r"re:\buart\b"]),
    ("MATLAB", ["matlab"]),
    ("Simulink", ["simulink"]),
    ("LabVIEW", ["labview"]),
    ("ROS", [r"re:\bros\s?2?\b(?=.{0,40}(?:robot|navigation|nodes|gazebo))", r"re:\bros2\b"]),
    ("Robotics", [r"re:\brobotics?\b"]),
    ("Device drivers / kernel", [r"re:\bdevice drivers?\b", r"re:\blinux kernel\b", r"re:\bkernel (?:drivers?|development|modules?)\b"]),
    ("Computer networking", [r"re:\btcp/ip\b", r"re:\bnetwork protocols?\b", r"re:\bbgp\b", r"re:\bospf\b",
                             r"re:\bnetwork engineering\b", r"re:\bsdn\b"]),
    ("Telecommunications", [r"re:\btelecom(?:munications?)?\b"]),
    ("Power electronics", [r"re:\bpower electronics\b", r"re:\bmotor control\b", r"re:\bbattery management\b"]),
    ("Analog/mixed-signal", [r"re:\banalog (?:design|circuits?|electronics)\b", r"re:\bmixed[\s\-]signal\b"]),
    ("Software-defined radio", [r"re:\bsoftware[\s\-]defined radio\b", r"cs:\bSDR\b", r"re:\bgnu ?radio\b"]),
    ("GNSS/GPS", [r"re:\bgnss\b", r"cs:\bGPS\b"], {"exclude": r"(?i)ride with gps"}),
    ("Test equipment", [r"re:\boscilloscopes?\b", r"re:\blogic analy[sz]ers?\b", r"re:\bspectrum analy[sz]ers?\b"]),
    ("Control systems", [r"re:\bcontrol systems?\b", r"re:\bcontrol theory\b", r"cs:\bPID\b"],
     {"exclude": r"(?i)(?:version|source|revision|internal|access|air traffic|quality)\s+control"}),
    ("Electrical engineering", [r"re:\belectrical engineering\b", r"re:\belectronics engineering\b"]),
    ("Semiconductors", [r"re:\bsemiconductors?\b", r"re:\bsilicon\b(?! valley)"]),
)

# ----------------------------------------------------------------- security
add("Security",
    ("Cybersecurity", [r"re:\bcyber[\s\-]?security\b", "infosec", r"re:\binformation security\b"]),
    ("Penetration testing", [r"re:\bpen(?:etration)?[\s\-]?test\w*", r"re:\bred team\w*"]),
    ("OWASP/AppSec", ["owasp", r"re:\bappsec\b", r"re:\bapplication security\b"]),
    ("IAM", [r"re:\biam\b", r"re:\bidentity and access\b"]),
    ("OAuth/SSO", ["oauth", "openid connect", r"re:\bsso\b", r"re:\bsaml\b"]),
    ("SOC 2 / compliance", [r"re:\bsoc\s?2\b", r"re:\biso\s?27001\b", r"re:\bhipaa\b", r"re:\bgdpr\b", r"re:\bpci[\s\-]dss\b"]),
    ("Cryptography", [r"re:\bcryptograph\w+", r"re:\bencryption\b"]),
    ("Security clearance", [r"re:\bsecurity clearance\b", r"re:\bts/sci\b", r"re:\bsecret clearance\b"]),
)

# --------------------------------------------------------------------- testing
add("Testing & QA",
    ("Unit testing / TDD", [r"re:\bunit test\w*", r"re:\btdd\b", r"re:\btest[\s\-]driven\b"]),
    ("Test automation", [r"re:\btest automation\b", r"re:\bautomated test\w*"]),
    ("Selenium", ["selenium"]),
    ("Cypress", [r"cs:\bCypress\b"]),
    ("Playwright", ["playwright"]),
    ("Jest", [r"cs:\bJest\b"]),
    ("pytest", ["pytest"]),
)

# ------------------------------------------------------ engineering practices
add("Practices & Architecture",
    ("Agile/Scrum", [r"re:\bagile\b", r"re:\bscrum\b", r"re:\bkanban\b"]),
    ("Distributed systems", [r"re:\bdistributed systems?\b"]),
    ("System design", [r"re:\bsystems? design\b", r"re:\bsoftware architecture\b"]),
    ("API design", [r"re:\bapi design\b"]),
    ("Event-driven architecture", [r"re:\bevent[\s\-]driven\b", r"re:\bevent sourcing\b", r"re:\bcqrs\b"]),
    ("Domain-driven design", [r"re:\bdomain[\s\-]driven\b", r"cs:\bDDD\b"]),
    ("Functional programming", [r"re:\bfunctional programming\b"]),
    ("Open source", [r"re:\bopen[\s\-]source\b"]),
    ("Code review", [r"re:\bcode reviews?\b"]),
    ("Performance optimization", [r"re:\bperformance (?:optimi[sz]ation|tuning)\b"]),
    ("Scalability", [r"re:\bscalab\w+", r"re:\bhigh[\s\-]availability\b"]),
)

# ------------------------------------------------------------ tools & products
add("Tools & Platforms",
    ("Git", [r"re:\bgit\b", r"re:\bgithub\b(?! actions)", r"re:\bversion control\b"]),
    ("Jira", ["jira"]),
    ("Figma", ["figma"]),
    ("Salesforce", ["salesforce"]),
    ("SAP", [r"cs:\bSAP\b"]),
    ("HubSpot", ["hubspot"]),
    ("Shopify", ["shopify"]),
    ("WordPress", ["wordpress"]),
    ("Stripe API", [r"re:\bstripe (?:api|integration|payments|connect|billing)\b"]),
    ("Unity/Unreal", [r"re:\bunity\s?3d\b", r"re:\bunity (?:game )?engine\b", r"re:\bunity developers?\b",
                      r"re:\bunreal(?: engine)?\b"]),
)

# ------------------------------------------------------ soft & language skills
add("Soft Skills & Languages",
    ("Communication", [r"re:\b(?:excellent|strong|good|great|clear)\s+(?:written\s+and\s+verbal\s+|verbal\s+and\s+written\s+)?communication\b",
                       r"re:\bcommunication skills\b", r"re:\bwritten and verbal\b", r"re:\bverbal and written\b"]),
    ("Leadership", [r"re:\b(?:technical|team|people|engineering|thought)\s+leadership\b",
                    r"re:\bleadership (?:skills|experience|qualities|abilities|role)\b",
                    r"re:\blead(?:ing)? (?:a |small |the )?(?:team|teams|engineers)\b", r"re:\bpeople management\b"]),
    ("Mentoring", [r"re:\bmentor(?:ing|ship)?\b"]),
    ("Problem solving", [r"re:\bproblem[\s\-]solv\w+"]),
    ("Cross-functional collaboration", [r"re:\bcross[\s\-]functional\b", r"re:\bteam player\b"]),
    ("Ownership mindset", [r"re:\b(?:take|taking|takes|sense of|high|extreme|full|end-to-end) ownership\b",
                           r"re:\bself[\s\-](?:starter|motivated|directed)\b", r"re:\bwork(?:ing)? autonomously\b"]),
    ("English proficiency", [r"re:\b(?:fluent|business|professional)\s+english\b", r"re:\benglish (?:fluency|proficiency|skills)\b"]),
    ("German language", [r"re:\bgerman\b(?=.{0,30}(?:language|speaking|fluent|skills|c1|b2|native|proficien))",
                         r"re:\b(?:fluent|native|business)\s+german\b", r"re:\bdeutschkenntnisse\b", r"re:\bflie(?:ß|ss)end\w* deutsch\b"]),
)

SKILLS = [t[0] for t in T]
CATEGORY = {t[0]: t[1] for t in T}
CATEGORIES = list(dict.fromkeys(t[1] for t in T))

# EXTC lens: skills taught in an Electronics & Telecommunication curriculum.
EXTC_CORE = [s for s, c in CATEGORY.items() if c == "Embedded, Hardware & Telecom"] + ["C", "C++", "Python"]

assert len(SKILLS) == len(set(SKILLS)), "duplicate skill names"
