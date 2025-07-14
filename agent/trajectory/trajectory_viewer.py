import json
from collections import defaultdict
from pathlib import Path
import os

class TrajectoryViewer:
    """
    用于查看和展示 trajectory 历史记录的工具。
    """

    def __init__(self, trajectories_dir: str = "trajectories"):
        """
        初始化 TrajectoryViewer。

        Args:
            trajectories_dir (str): 存储 trajectory 文件的目录。
        """
        self.trajectories_dir = Path(trajectories_dir)
        if not self.trajectories_dir.exists():
            raise FileNotFoundError(f"Trajectory directory not found: {self.trajectories_dir.resolve()}")

    def _find_trajectory_file(self, session_id: str) -> Path:
        """
        根据 session_id 查找对应的 trajectory 文件。
        支持多种命名格式，如 'session_{session_id}.jsonl' 或 'example_session_hook_{session_id}.jsonl'。
        """
        for file_path in self.trajectories_dir.glob(f"*{session_id}*.jsonl"):
            return file_path
        raise FileNotFoundError(f"No trajectory file found for session_id '{session_id}' in {self.trajectories_dir}")

    def _load_events(self, file_path: Path) -> list:
        """从 .jsonl 文件加载事件。"""
        events = []
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    events.append(json.loads(line))
        return events

    def _group_by_trace(self, events: list) -> dict:
        """按 trace_id 对事件进行分组。"""
        grouped_events = defaultdict(list)
        for event in events:
            trace_id = event.get("trace_id", "unknown_trace")
            grouped_events[trace_id].append(event)
        
        # 对每个 trace 内的事件按时间戳排序
        for trace_id in grouped_events:
            grouped_events[trace_id].sort(key=lambda e: e.get("timestamp", ""))
            
        return grouped_events

    def display(self, session_id: str):
        """
        显示指定 session_id 的 trajectory 历史。

        Args:
            session_id (str): 要显示的会话ID。
        """
        try:
            file_path = self._find_trajectory_file(session_id)
            print(f"🔎 Found trajectory file: {file_path}")
            print(f"\n{'='*60}")
            print(f"📜 Trajectory for Session ID: {session_id}")
            print(f"{'='*60}\n")

            events = self._load_events(file_path)
            if not events:
                print("No events found in the trajectory file.")
                return

            grouped_events = self._group_by_trace(events)

            # 按第一个事件的时间戳对 trace_id 进行排序
            sorted_trace_ids = sorted(grouped_events.keys(), 
                                      key=lambda tid: grouped_events[tid][0].get("timestamp", "") if grouped_events[tid] else "")

            for trace_id in sorted_trace_ids:
                print(f"--- Trace ID: {trace_id} ---")
                trace_events = grouped_events[trace_id]
                
                for event in trace_events:
                    timestamp = event.get("timestamp", "N/A")
                    event_type = event.get("event_type", "unknown")
                    span_id = event.get("span_id", "N/A")
                    parent_span_id = event.get("parent_span_id", "None")
                    data = json.dumps(event.get("data", {}), ensure_ascii=False, indent=2)
                    
                    print(f"\n[{timestamp}] 🔹 {event_type}")
                    print(f"  - Span ID: {span_id}")
                    print(f"  - Parent Span ID: {parent_span_id}")
                    print(f"  - Data:\n{self._indent_text(data, 4)}")
                
                print(f"\n--- End of Trace ---")
            
            print(f"\n{'='*60}")
            print("✅ Trajectory display finished.")
            print(f"{'='*60}\n")

        except FileNotFoundError as e:
            print(f"Error: {e}")
        except Exception as e:
            print(f"An unexpected error occurred: {e}")

    def _indent_text(self, text: str, spaces: int) -> str:
        """辅助函数，用于缩进多行文本。"""
        return "".join(" " * spaces + line for line in text.splitlines(True))

def main():
    """
    提供一个命令行接口来查看 trajectory。
    """
    import argparse
    parser = argparse.ArgumentParser(description="Display trajectory history for a given session ID.")
    parser.add_argument("session_id", help="The session ID to display the trajectory for.")
    parser.add_argument("--dir", default="trajectories", help="The directory where trajectory files are stored.")
    
    args = parser.parse_args()
    
    # 确保脚本可以从项目根目录运行
    # python -m agent.trajectory.trajectory_viewer <session_id>
    project_root = Path(__file__).parent.parent.parent
    trajectories_path = project_root / args.dir

    viewer = TrajectoryViewer(trajectories_dir=str(trajectories_path))
    viewer.display(args.session_id)

if __name__ == "__main__":
    main()