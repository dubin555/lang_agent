"""Example usage of the stateless, event-based trajectory recorder."""

import asyncio
import sys
import os
from typing import List, Annotated, TypedDict
from pathlib import Path

# Add the project root to the Python path to allow absolute imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from langchain_core.messages import HumanMessage, AIMessage, BaseMessage
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages

from agent.trajectory.langgraph_hook import create_trajectory_node
from agent.trajectory.react_trajectory_hook import create_trajectory_hook
from agent.trajectory.trajectory_recorder import create_local_recorder
from agent.trajectory.trajectory_viewer import TrajectoryViewer


# Define the state for the graph correctly.
# Using TypedDict and Annotated allows LangGraph to correctly manage message history.
class AgentState(TypedDict):
    messages: Annotated[List[BaseMessage], add_messages]
    session_id: str


# Example 1: Using TrajectoryNode in a custom graph
async def example_with_node():
    """Demonstrates using TrajectoryNode within a custom StateGraph."""
    print("--- Running Example 1: TrajectoryNode ---")

    # Node functions now correctly append to the message history
    async def agent_node(state: AgentState) -> dict:
        return {"messages": [AIMessage(content="I can help with that.")]}

    async def tool_node(state: AgentState) -> dict:
        return {"messages": [AIMessage(content="Here are the tool results...")]}

    # 1. Create a recorder instance
    recorder = create_local_recorder()

    # 2. Create the trajectory node, passing the recorder to it
    trajectory_node = create_trajectory_node(recorder)

    # Build the graph
    workflow = StateGraph(AgentState)
    workflow.add_node("agent", agent_node)
    workflow.add_node("tools", tool_node)
    workflow.add_node("trajectory", trajectory_node)  # Add the observer node

    # Define the flow, ensuring the trajectory node is called after each step
    workflow.set_entry_point("agent")
    workflow.add_edge("agent", "trajectory")
    workflow.add_edge("trajectory", "tools")
    workflow.add_edge("tools", END)

    app = workflow.compile()

    # Run the graph
    initial_state = {
        "messages": [HumanMessage(content="Hello!")],
        "session_id": "example_session_node_123",
    }

    await app.ainvoke(initial_state)
    print(
        "Execution finished. Trajectory recorded to 'trajectories/example_session_node_123.jsonl'"
    )


# Example 2: Using ReactTrajectoryHook with a prebuilt agent
async def example_with_hook():
    """Demonstrates using ReactTrajectoryHook with a prebuilt agent."""
    print("\n--- Running Example 2: ReactTrajectoryHook ---")

    try:
        from langgraph.prebuilt import create_react_agent

        # This import is assumed to exist for the example.
        from agent.llm_provider import init_llm
    except ImportError:
        print(
            "Skipping example_with_hook: `langgraph.prebuilt` or `agent.llm_provider` not available."
        )
        return

    # NOTE: This example requires a configured LLM (e.g., OpenAI API key).
    llm = init_llm()
    # Define your tools here for the agent to use.
    tools = []

    # 1. Create a recorder instance
    recorder = create_local_recorder()

    # 2. Create the trajectory hook, passing the recorder to it
    trajectory_hook = create_trajectory_hook(recorder)

    # 3. Create the agent with the post_model_hook
    agent = create_react_agent(
        llm,
        tools,
        post_model_hook=trajectory_hook,
    )

    # Run the agent for multiple turns
    config = {"configurable": {"thread_id": "example_session_hook_456"}}

    print("\n--- Turn 1 ---")
    await agent.ainvoke(
        {"messages": [HumanMessage(content="Hello! What is the weather in SF?")]},
        config,
    )

    print("\n--- Turn 2 ---")
    await agent.ainvoke(
        {"messages": [HumanMessage(content="Thanks! What about in LA?")]},
        config,
    )

    print(
        "\nExecution finished. Trajectory recorded to 'trajectories/example_session_hook_456.jsonl'"
    )


async def main():
    # --- Optional: Clean up old trajectory files for a fresh run ---
    print("--- Cleaning up old trajectory files ---")
    for f in Path("trajectories").glob("*.jsonl"):
        try:
            f.unlink()
        except OSError as e:
            print(f"Error removing file {f}: {e}")

    # --- Run Examples ---
    await example_with_node()
    await example_with_hook()

    # --- Display the generated trajectories ---
    print("\n" + "="*60)
    print("🔍 Displaying Generated Trajectories")
    print("="*60)

    try:
        viewer = TrajectoryViewer(trajectories_dir="trajectories")

        print("\n--- Trajectory for Example 1 (TrajectoryNode) ---")
        viewer.display("example_session_node_123")

        print("\n--- Trajectory for Example 2 (ReactTrajectoryHook) ---")
        viewer.display("example_session_hook_456")

    except FileNotFoundError as e:
        print(f"\nCould not display trajectories: {e}")
    except Exception as e:
        print(f"\nAn unexpected error occurred while displaying trajectories: {e}")


if __name__ == "__main__":
    asyncio.run(main())