"""
Workflow Visualization Graph Generator
Converts SOP steps, decision points, and exceptions into React Flow nodes and edges.
"""
from typing import Dict, Any, List
from packages.schemas.models import SOP

class WorkflowGenerator:
    @staticmethod
    def generate_flow_graph(sop: SOP) -> Dict[str, Any]:
        nodes = []
        edges = []

        # Start Node
        nodes.append({
            "id": "node_start",
            "type": "input",
            "data": {"label": f"Start: {sop.title}"},
            "position": {"x": 250, "y": 0}
        })

        y_offset = 100
        prev_node_id = "node_start"

        for idx, step in enumerate(sop.steps, 1):
            curr_id = f"node_step_{idx}"
            nodes.append({
                "id": curr_id,
                "type": "default",
                "data": {
                    "label": f"Step {step.step_number}: {step.title}\n({step.responsible_role})",
                    "role": step.responsible_role,
                    "description": step.description
                },
                "position": {"x": 250, "y": y_offset}
            })

            edges.append({
                "id": f"edge_{prev_node_id}_{curr_id}",
                "source": prev_node_id,
                "target": curr_id,
                "animated": True
            })

            # Check if this step has a decision branch (e.g. KYC)
            if "kyc" in step.title.lower() or "verif" in step.title.lower():
                decision_id = f"node_decision_{idx}"
                y_offset += 100
                nodes.append({
                    "id": decision_id,
                    "type": "default",
                    "data": {"label": f"{step.title} Approved?"},
                    "position": {"x": 250, "y": y_offset}
                })
                edges.append({
                    "id": f"edge_{curr_id}_{decision_id}",
                    "source": curr_id,
                    "target": decision_id
                })

                # Branch NO: Exception / Resolve
                exception_id = f"node_exc_{idx}"
                nodes.append({
                    "id": exception_id,
                    "type": "output",
                    "data": {"label": "NO: Halt & Resolve Issue (Compliance Escalation)"},
                    "position": {"x": 50, "y": y_offset + 90}
                })
                edges.append({
                    "id": f"edge_{decision_id}_{exception_id}",
                    "source": decision_id,
                    "target": exception_id,
                    "label": "Fail"
                })

                prev_node_id = decision_id

            else:
                prev_node_id = curr_id

            y_offset += 100

        # End Node
        end_node_id = "node_complete"
        nodes.append({
            "id": end_node_id,
            "type": "output",
            "data": {"label": f"Completed: {sop.expected_output or 'Process Finished'}"},
            "position": {"x": 250, "y": y_offset}
        })
        edges.append({
            "id": f"edge_{prev_node_id}_{end_node_id}",
            "source": prev_node_id,
            "target": end_node_id,
            "label": "Pass"
        })

        return {"nodes": nodes, "edges": edges}

workflow_generator = WorkflowGenerator()
