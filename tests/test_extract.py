"""Unit tests for the tricky parts of skill extraction. Run with: pytest -q"""
from hiresignal.extract import extract


def has(text, skill):
    return skill in extract(text)


def test_languages_with_symbols():
    t = "We use C++, C# and Python with Docker."
    assert has(t, "C++") and has(t, "C#") and has(t, "Python")


def test_java_vs_javascript():
    assert has("Strong JavaScript and React skills, Docker", "JavaScript")
    assert not has("Strong JavaScript and React skills, Docker", "Java")
    assert has("Backend in Java and Kotlin with Kafka", "Java")


def test_go_language_vs_verb():
    assert has("Our backend is written in Go, with PostgreSQL and Kubernetes.", "Go")
    assert not has("You will go to market with our sales team. We use Python and AWS.", "Go")
    assert has("Services in golang with Redis and Docker", "Go")


def test_c_language_vs_series_c():
    assert has("Firmware in C on ARM microcontrollers with FreeRTOS", "C")
    assert not has("We raised our Series C. Stack: Python, React, AWS.", "C")


def test_r_language_vs_rnd():
    assert has("Data science with Python, R and SQL", "R")
    assert not has("Join our R&D team working on Python and AWS", "R")


def test_react_vs_react_native():
    t = "Mobile app in React Native with TypeScript"
    assert has(t, "React Native") and not has(t, "React")


def test_no_false_rest():
    assert not has("For the rest of the team we use Python and Django", "REST APIs")
    assert has("Design RESTful services in Python", "REST APIs")


def test_genai_terms():
    t = "Build RAG pipelines with LangChain, embeddings and a vector database for our LLM agents."
    for s in ["RAG", "LangChain", "Embeddings", "Vector databases", "LLMs"]:
        assert has(t, s), s


def test_extc_terms():
    t = "Embedded firmware engineer: STM32, FreeRTOS, SPI, I2C, PCB bring-up with oscilloscopes, Verilog on FPGA."
    for s in ["Firmware", "Microcontrollers", "RTOS", "I2C/SPI/UART", "PCB design",
              "Test equipment", "Verilog/SystemVerilog", "FPGA"]:
        assert has(t, s), s


def test_postgres_not_counted_as_sql():
    assert not has("We use PostgreSQL and NoSQL stores with Python", "SQL")
