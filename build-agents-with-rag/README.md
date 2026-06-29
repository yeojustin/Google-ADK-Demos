Source https://codelabs.developers.google.com/codelabs/production-ready-ai-with-gc/7-advanced-agent-capabilities/building-agents-with-retrieval-augmented-generation#0

1. Introduction
   Overview
   The goal of this lab is to learn how to develop end-to-end Agentic Retrieval-Augmented Generation (RAG) applications in Google Cloud. In this lab, you will build a financial analysis agent that can answer questions by combining information from two different sources: unstructured documents (Alphabet's quarterly SEC filings - financial statements and operational details that every public company in the U.S. submits to the Securities and Exchange Commission), and structured data (historical stock prices).

You will use Vertex AI Search to build a powerful semantic search engine for the unstructured financial reports. For the structured data, you will create a custom Python tool. Finally, you will use the Agent Development Kit (ADK) to build an intelligent agent that can reason about a user's query, decide which tool to use, and synthesize the information into a coherent answer.

What you'll do
Set up a Vertex AI Search data store for semantic search over private documents.
Create a custom Python function as a tool for an agent.
Use the Agent Development Kit (ADK) to build a multi-tool agent.
Combine retrieval from unstructured and structured data sources to answer complex questions.
Test and interact with an agent that exhibits reasoning capabilities.
What you'll learn
In this lab, you will learn:

The core concepts of Retrieval-Augmented Generation (RAG) and Agentic RAG.
How to implement semantic search over documents using Vertex AI Search.
How to expose structured data to an agent by creating custom tools.
How to build and orchestrate a multi-tool agent with the Agent Development Kit (ADK).
How agents use reasoning and planning to answer complex questions using multiple data sources.
