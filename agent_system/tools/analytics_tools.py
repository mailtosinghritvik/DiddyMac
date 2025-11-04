"""
Custom Analytics Tools for DDMac Analytics Agents
Uses separate DDMac Analytics Supabase database
"""
from agents import function_tool
import os
import sys
from dotenv import load_dotenv
from typing import Optional

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

load_dotenv()

from utils.ddmac_analytics_client import DDMacAnalyticsClient

# ============================================================================
# EMPLOYEE ANALYTICS TOOLS
# ============================================================================

@function_tool
async def get_employee_summary(user_id: int, start_date: Optional[str] = None, end_date: Optional[str] = None) -> str:
    """
    Get comprehensive employee summary including hours worked, productivity, and client distribution.
    
    Args:
        user_id: Employee user ID from the database (required)
        start_date: Start date in YYYY-MM-DD format (optional, defaults to all time)
        end_date: End date in YYYY-MM-DD format (optional, defaults to all time)
    
    Returns:
        Formatted text summary of employee metrics and performance
    """
    try:
        client = DDMacAnalyticsClient()
        
        # Call the comprehensive employee analytics RPC
        result = client.execute_rpc(
            'get_comprehensive_employee_analytics',
            {
                'start_date_param': start_date,
                'end_date_param': end_date
            }
        )
        
        if not result:
            return f"❌ No data found for employee ID {user_id}"
        
        # Filter for specific employee
        employee_data = [emp for emp in result if emp.get('employee_id') == user_id]
        
        if not employee_data:
            return f"❌ No data found for employee ID {user_id}"
        
        emp = employee_data[0]
        
        # Format response
        period_str = f"{start_date or 'All time'} to {end_date or 'Present'}"
        
        summary = f"""Employee Summary - {emp.get('employee_name', 'Unknown')}

Work Period: {period_str}
Total Hours: {emp.get('total_work_hours', 0):.1f} hours
Days Worked: {emp.get('actual_work_days', 0)} days
Avg Hours/Day: {emp.get('average_daily_hours', 0):.1f} hours

Clients Worked: {len(emp.get('client_list', []))} clients
Tasks Completed: {len(emp.get('task_list', []))} tasks

Utilization Rate: {emp.get('utilization_rate', 0):.1f}%
Performance: {'High Performance' if emp.get('utilization_rate', 0) >= 90 else 'Good Performance' if emp.get('utilization_rate', 0) >= 75 else 'Needs Improvement'}
"""
        
        return summary
        
    except Exception as e:
        return f"❌ Error fetching employee summary: {str(e)}"

@function_tool
async def get_all_employees_overview(start_date: Optional[str] = None, end_date: Optional[str] = None) -> str:
    """
    Get overview of all employees including team metrics and top performers.
    
    Args:
        start_date: Start date in YYYY-MM-DD format (optional)
        end_date: End date in YYYY-MM-DD format (optional)
    
    Returns:
        Formatted text summary of all employees and team metrics
    """
    try:
        client = DDMacAnalyticsClient()
        
        # Get all employees data
        result = client.execute_rpc(
            'get_comprehensive_employee_analytics',
            {
                'start_date_param': start_date,
                'end_date_param': end_date
            }
        )
        
        if not result:
            return "❌ No employee data available"
        
        # Calculate team metrics
        total_employees = len(result)
        total_hours = sum(emp.get('total_work_hours', 0) for emp in result)
        avg_hours = total_hours / total_employees if total_employees > 0 else 0
        avg_utilization = sum(emp.get('utilization_rate', 0) for emp in result) / total_employees if total_employees > 0 else 0
        
        # Get top performers
        sorted_employees = sorted(result, key=lambda x: x.get('total_work_hours', 0), reverse=True)
        top_5 = sorted_employees[:5]
        
        period_str = f"{start_date or 'All time'} to {end_date or 'Present'}"
        
        summary = f"""Team Overview

Period: {period_str}
Active Employees: {total_employees}
Total Team Hours: {total_hours:.1f} hours
Avg Hours/Employee: {avg_hours:.1f} hours
Avg Utilization: {avg_utilization:.1f}%

Top 5 Performers (by hours):
"""
        
        for i, emp in enumerate(top_5, 1):
            summary += f"{i}. {emp.get('employee_name', 'Unknown')}: {emp.get('total_work_hours', 0):.1f} hrs ({emp.get('utilization_rate', 0):.1f}% utilization)\n"
        
        return summary
        
    except Exception as e:
        return f"❌ Error fetching team overview: {str(e)}"

@function_tool
async def get_employee_client_breakdown(user_id: int, start_date: Optional[str] = None, end_date: Optional[str] = None) -> str:
    """
    Get detailed client time distribution for a specific employee.
    
    Args:
        user_id: Employee user ID (required)
        start_date: Start date in YYYY-MM-DD format (optional)
        end_date: End date in YYYY-MM-DD format (optional)
    
    Returns:
        Formatted breakdown of hours per client with statistics
    """
    try:
        client = DDMacAnalyticsClient()
        
        # Get client time distribution
        result = client.execute_rpc(
            'get_user_client_time_distribution',
            {
                'user_id_param': user_id,
                'start_date_param': start_date or '2020-01-01',
                'end_date_param': end_date or '2100-01-01'
            }
        )
        
        if not result:
            return f"❌ No client distribution data for employee ID {user_id}"
        
        # Sort by total hours
        sorted_clients = sorted(result, key=lambda x: x.get('total_hours', 0), reverse=True)
        
        total_hours = sum(c.get('total_hours', 0) for c in sorted_clients)
        
        summary = f"""Client Time Distribution - Employee ID {user_id}

Period: {start_date or 'All time'} to {end_date or 'Present'}
Total Hours: {total_hours:.1f} hours
Unique Clients: {len(sorted_clients)}

Top Clients:
"""
        
        for i, c in enumerate(sorted_clients[:10], 1):
            client_name = c.get('client_name', 'Unknown')
            hours = c.get('total_hours', 0)
            sessions = c.get('sessions', 0)
            avg_session = c.get('avg_session_hours', 0)
            pct = (hours / total_hours * 100) if total_hours > 0 else 0
            
            summary += f"{i}. {client_name}: {hours:.1f} hrs ({pct:.1f}%) - {sessions} sessions, {avg_session:.1f}h avg\n"
        
        return summary
        
    except Exception as e:
        return f"❌ Error fetching client breakdown: {str(e)}"

@function_tool
async def get_employee_productivity_score(user_id: int) -> str:
    """
    Get productivity score and performance rating for an employee.
    
    Args:
        user_id: Employee user ID (required)
    
    Returns:
        Productivity score with performance category
    """
    try:
        client = DDMacAnalyticsClient()
        
        # Get employee summary
        result = client.execute_rpc(
            'get_comprehensive_employee_analytics',
            {
                'start_date_param': None,
                'end_date_param': None
            }
        )
        
        employee_data = [emp for emp in result if emp.get('employee_id') == user_id]
        
        if not employee_data:
            return f"❌ No data found for employee ID {user_id}"
        
        emp = employee_data[0]
        utilization = emp.get('utilization_rate', 0)
        
        # Categorize performance
        if utilization >= 95:
            category = "Excellent"
            emoji = "🌟"
        elif utilization >= 85:
            category = "Good"
            emoji = "✅"
        elif utilization >= 75:
            category = "Satisfactory"
            emoji = "👍"
        else:
            category = "Needs Improvement"
            emoji = "⚠️"
        
        return f"""{emoji} Productivity Score - {emp.get('employee_name', 'Unknown')}

Utilization Rate: {utilization:.1f}%
Performance Category: {category}
Total Hours: {emp.get('total_work_hours', 0):.1f} hrs
Days Worked: {emp.get('actual_work_days', 0)} days
Daily Average: {emp.get('average_daily_hours', 0):.1f} hrs/day
"""
        
    except Exception as e:
        return f"❌ Error calculating productivity: {str(e)}"

# ============================================================================
# PROJECT ANALYTICS TOOLS
# ============================================================================

@function_tool
async def get_project_overview(job_name: str) -> str:
    """
    Get comprehensive project overview with budget, progress, and team information.
    
    Args:
        job_name: Name of the project/job (required)
    
    Returns:
        Formatted project summary with key metrics
    """
    try:
        client = DDMacAnalyticsClient()
        
        # Get project estimates from accubid_breakdowns
        estimates = client.query_table(
            "accubid_breakdowns",
            "task_name, time_estimate, cost_estimate",
            {"job_name": job_name}
        )
        
        if not estimates:
            return f"❌ No data found for project: {job_name}"
        
        # Calculate totals
        # Find EVERYTHING task for total estimate
        everything_tasks = [e for e in estimates if 'EVERYTHING' in e.get('task_name', '').upper()]
        if everything_tasks:
            total_estimate = sum(e.get('time_estimate', 0) for e in everything_tasks)
            total_cost_estimate = sum(e.get('cost_estimate', 0) for e in everything_tasks)
        else:
            # Sum all tasks if no EVERYTHING task
            total_estimate = sum(e.get('time_estimate', 0) for e in estimates)
            total_cost_estimate = sum(e.get('cost_estimate', 0) for e in estimates)
        
        # Get actual hours from timesheets
        job_id_result = client.query_table("jobcodes", "id", {"name": job_name})
        actual_hours = 0
        
        if job_id_result:
            job_id = job_id_result[0].get('id')
            timesheets = client.query_table("timesheets", "duration", {"jobcode_id": job_id})
            total_seconds = sum(t.get('duration', 0) for t in timesheets)
            actual_hours = total_seconds / 3600
        
        # Calculate metrics
        completion_pct = (actual_hours / total_estimate * 100) if total_estimate > 0 else 0
        variance = actual_hours - total_estimate
        variance_pct = (variance / total_estimate * 100) if total_estimate > 0 else 0
        
        budget_status = "✅ Under Budget" if variance < 0 else "⚠️ Over Budget" if variance > 0 else "On Budget"
        
        summary = f"""Project Overview - {job_name}

Budget Status: {budget_status}

Estimated Hours: {total_estimate:.1f} hrs
Actual Hours: {actual_hours:.1f} hrs
Variance: {variance:+.1f} hrs ({variance_pct:+.1f}%)
Completion: {completion_pct:.1f}%

Estimated Cost: ${total_cost_estimate:,.2f}
Total Tasks: {len(estimates)}
"""
        
        return summary
        
    except Exception as e:
        return f"❌ Error fetching project overview: {str(e)}"

@function_tool
async def get_project_budget_analysis(job_name: str) -> str:
    """
    Analyze project budget with detailed variance breakdown by task.
    
    Args:
        job_name: Name of the project/job (required)
    
    Returns:
        Budget analysis with tasks over/under budget
    """
    try:
        client = DDMacAnalyticsClient()
        
        # Get task estimates (excluding EVERYTHING)
        estimates = client.query_table(
            "accubid_breakdowns",
            "id, task_name, time_estimate, cost_estimate",
            {"job_name": job_name}
        )
        
        # Filter out EVERYTHING tasks
        task_estimates = [e for e in estimates if 'EVERYTHING' not in e.get('task_name', '').upper()]
        
        if not task_estimates:
            return f"❌ No task data for project: {job_name}"
        
        # Get job ID for actual hours
        job_id_result = client.query_table("jobcodes", "id", {"name": job_name})
        
        if not job_id_result:
            return f"⚠️ Project '{job_name}' found in estimates but not in jobcodes"
        
        job_id = job_id_result[0].get('id')
        
        # Get all timesheets for this job
        timesheets = client.query_table("timesheets", "duration, user_id", {"jobcode_id": job_id})
        total_actual_hours = sum(t.get('duration', 0) for t in timesheets) / 3600
        total_estimate_hours = sum(t.get('time_estimate', 0) for t in task_estimates)
        
        # Calculate variances
        over_budget_tasks = []
        under_budget_tasks = []
        
        for task in task_estimates[:10]:  # Top 10 tasks
            task_name = task.get('task_name', 'Unknown')
            estimate = task.get('time_estimate', 0)
            
            # For individual task actuals, we'd need task-level tracking
            # For now, show estimates
            if estimate > 0:
                under_budget_tasks.append((task_name, estimate))
        
        total_variance = total_actual_hours - total_estimate_hours
        variance_pct = (total_variance / total_estimate_hours * 100) if total_estimate_hours > 0 else 0
        
        summary = f"""Budget Analysis - {job_name}

Overall Budget:
Estimated: {total_estimate_hours:.1f} hrs
Actual: {total_actual_hours:.1f} hrs
Variance: {total_variance:+.1f} hrs ({variance_pct:+.1f}%)
Status: {'⚠️ Over Budget' if total_variance > 0 else '✅ Under Budget'}

Total Tasks: {len(task_estimates)}
Estimated Cost: ${sum(t.get('cost_estimate', 0) for t in task_estimates):,.2f}

Top Tasks by Estimate:
"""
        
        for i, (task_name, estimate) in enumerate(sorted(under_budget_tasks, key=lambda x: x[1], reverse=True)[:5], 1):
            summary += f"{i}. {task_name}: {estimate:.1f} hrs\n"
        
        return summary
        
    except Exception as e:
        return f"❌ Error analyzing budget: {str(e)}"

@function_tool
async def get_all_projects_status() -> str:
    """
    Get status overview of all projects including budget and progress.
    
    Returns:
        Summary of all projects with key metrics
    """
    try:
        client = DDMacAnalyticsClient()
        
        # Get all jobs
        jobs = client.get_job_list()
        
        if not jobs:
            return "❌ No projects found"
        
        summary = f"""All Projects Status

Total Projects: {len(jobs)}

Projects Summary:
"""
        
        for i, job in enumerate(jobs[:15], 1):  # Top 15 projects
            job_name = job.get('name', 'Unknown')
            job_id = job.get('id')
            
            # Get estimates for this job
            estimates = client.query_table("accubid_breakdowns", "time_estimate", {"job_name": job_name})
            everything_tasks = [e for e in estimates if 'EVERYTHING' in str(e.get('task_name', '')).upper()]
            
            if everything_tasks:
                estimated_hours = sum(e.get('time_estimate', 0) for e in everything_tasks)
            else:
                estimated_hours = sum(e.get('time_estimate', 0) for e in estimates)
            
            # Get actuals
            timesheets = client.query_table("timesheets", "duration", {"jobcode_id": job_id})
            actual_hours = sum(t.get('duration', 0) for t in timesheets) / 3600
            
            completion = (actual_hours / estimated_hours * 100) if estimated_hours > 0 else 0
            status_emoji = "🟢" if completion < 80 else "🟡" if completion < 100 else "🔴"
            
            summary += f"{i}. {status_emoji} {job_name}: {actual_hours:.1f}/{estimated_hours:.1f} hrs ({completion:.0f}%)\n"
        
        return summary
        
    except Exception as e:
        return f"❌ Error fetching projects status: {str(e)}"

@function_tool
async def get_project_team_hours(job_name: str) -> str:
    """
    Get team member hours breakdown for a specific project.
    
    Args:
        job_name: Name of the project/job (required)
    
    Returns:
        Breakdown of hours by team member
    """
    try:
        client = DDMacAnalyticsClient()
        
        # Get job ID
        job_id_result = client.query_table("jobcodes", "id", {"name": job_name})
        
        if not job_id_result:
            return f"❌ Project not found: {job_name}"
        
        job_id = job_id_result[0].get('id')
        
        # Get timesheets for this job grouped by user
        timesheets = client.query_table("timesheets", "user_id, duration", {"jobcode_id": job_id})
        
        if not timesheets:
            return f"⚠️ No time tracking data for project: {job_name}"
        
        # Group by user
        user_hours = {}
        for ts in timesheets:
            user_id = ts.get('user_id')
            duration = ts.get('duration', 0) / 3600  # Convert to hours
            user_hours[user_id] = user_hours.get(user_id, 0) + duration
        
        # Get user names
        users = client.query_table("users", "id, username")
        user_map = {u.get('id'): u.get('username', 'Unknown') for u in users}
        
        # Sort by hours
        sorted_users = sorted(user_hours.items(), key=lambda x: x[1], reverse=True)
        
        total_hours = sum(user_hours.values())
        
        summary = f"""Team Hours - {job_name}

Total Team Hours: {total_hours:.1f} hours
Team Members: {len(sorted_users)}

Hours by Team Member:
"""
        
        for i, (user_id, hours) in enumerate(sorted_users, 1):
            username = user_map.get(user_id, f'User {user_id}')
            pct = (hours / total_hours * 100) if total_hours > 0 else 0
            summary += f"{i}. {username}: {hours:.1f} hrs ({pct:.1f}%)\n"
        
        return summary
        
    except Exception as e:
        return f"❌ Error fetching team hours: {str(e)}"

# ============================================================================
# TASK ANALYTICS TOOLS
# ============================================================================

@function_tool
async def get_task_variance_analysis(job_name: str) -> str:
    """
    Analyze task-level variance between estimated and actual hours for a project.
    
    Args:
        job_name: Name of the project/job (required)
    
    Returns:
        Variance analysis showing tasks over/under budget
    """
    try:
        client = DDMacAnalyticsClient()
        
        # Get task summary using RPC
        result = client.execute_rpc(
            'get_accubid_task_summary',
            {
                'p_limit': 100,
                'p_offset': 0,
                'p_job_name': job_name,
                'p_user_id': None,
                'p_jobcode_id': None
            }
        )
        
        if not result:
            return f"❌ No task data for project: {job_name}"
        
        # Filter out EVERYTHING tasks
        tasks = [t for t in result if 'EVERYTHING' not in t.get('task_name', '').upper()]
        
        if not tasks:
            return f"⚠️ No individual tasks found for: {job_name}"
        
        # Calculate variances
        task_variances = []
        
        for task in tasks:
            task_name = task.get('task_name', 'Unknown')
            estimate = task.get('time_estimate', 0)
            actual = task.get('duration_hours', 0)
            
            variance = actual - estimate
            variance_pct = (variance / estimate * 100) if estimate > 0 else 0
            
            task_variances.append({
                'name': task_name,
                'estimate': estimate,
                'actual': actual,
                'variance': variance,
                'variance_pct': variance_pct
            })
        
        # Sort by absolute variance
        sorted_tasks = sorted(task_variances, key=lambda x: abs(x['variance']), reverse=True)
        
        over_budget = [t for t in sorted_tasks if t['variance'] > 0]
        under_budget = [t for t in sorted_tasks if t['variance'] < 0]
        
        summary = f"""Task Variance Analysis - {job_name}

Total Tasks: {len(tasks)}
Over Budget Tasks: {len(over_budget)}
Under Budget Tasks: {len(under_budget)}

Top Tasks Over Budget:
"""
        
        for i, task in enumerate(over_budget[:5], 1):
            summary += f"{i}. {task['name']}: +{task['variance']:.1f} hrs ({task['variance_pct']:+.1f}%)\n"
        
        summary += "\nTop Tasks Under Budget:\n"
        
        for i, task in enumerate(under_budget[:5], 1):
            summary += f"{i}. {task['name']}: {task['variance']:.1f} hrs ({task['variance_pct']:.1f}%)\n"
        
        return summary
        
    except Exception as e:
        return f"❌ Error analyzing task variance: {str(e)}"

@function_tool
async def get_task_progress_status(job_name: str) -> str:
    """
    Get foreman progress status for all tasks in a project.
    
    Args:
        job_name: Name of the project/job (required)
    
    Returns:
        Task progress comparison with foreman vs actual completion
    """
    try:
        client = DDMacAnalyticsClient()
        
        # Get tasks for this job
        tasks = client.query_table(
            "accubid_breakdowns",
            "id, task_name, time_estimate",
            {"job_name": job_name}
        )
        
        # Filter out EVERYTHING
        tasks = [t for t in tasks if 'EVERYTHING' not in t.get('task_name', '').upper()]
        
        if not tasks:
            return f"❌ No tasks found for project: {job_name}"
        
        summary = f"""Task Progress Status - {job_name}

Total Tasks: {len(tasks)}

"""
        
        tasks_with_progress = 0
        
        for task in tasks[:15]:  # Top 15 tasks
            task_id = task.get('id')
            task_name = task.get('task_name', 'Unknown')
            
            # Get latest foreman progress
            progress = client.get_latest_task_progress(task_id)
            
            if progress is not None:
                tasks_with_progress += 1
                status = "🟢" if progress >= 75 else "🟡" if progress >= 50 else "🔴"
                summary += f"{status} {task_name}: {progress:.0f}% complete\n"
            else:
                summary += f"⚪ {task_name}: No progress reported\n"
        
        summary += f"\nTasks with Progress Updates: {tasks_with_progress}/{len(tasks)}"
        
        return summary
        
    except Exception as e:
        return f"❌ Error fetching task progress: {str(e)}"

@function_tool
async def update_foreman_task_progress(task_id: int, progress_percent: float) -> str:
    """
    Update foreman progress for a specific task.
    
    Args:
        task_id: Task ID from accubid_breakdowns table (required)
        progress_percent: Progress percentage 0-100 (required)
    
    Returns:
        Confirmation of progress update
    """
    try:
        # Validate progress
        if not 0 <= progress_percent <= 100:
            return f"❌ Invalid progress: {progress_percent}. Must be between 0-100"
        
        client = DDMacAnalyticsClient()
        
        # Get task details
        task_result = client.query_table("accubid_breakdowns", "task_name, job_name", filters={"id": task_id})
        
        if not task_result:
            return f"❌ Task ID {task_id} not found"
        
        task_info = task_result[0]
        
        # Insert progress update
        result = client.insert_task_progress(task_id, progress_percent)
        
        return f"""✅ Foreman Progress Updated

Task: {task_info.get('task_name', 'Unknown')}
Project: {task_info.get('job_name', 'Unknown')}
Progress: {progress_percent:.0f}%
Updated: Successfully recorded
"""
        
    except Exception as e:
        return f"❌ Error updating progress: {str(e)}"

@function_tool
async def get_task_efficiency_summary(job_name: str) -> str:
    """
    Calculate efficiency metrics for all tasks in a project.
    
    Args:
        job_name: Name of the project/job (required)
    
    Returns:
        Efficiency summary with task performance ratings
    """
    try:
        client = DDMacAnalyticsClient()
        
        # Get task data
        result = client.execute_rpc(
            'get_accubid_task_summary',
            {
                'p_limit': 100,
                'p_offset': 0,
                'p_job_name': job_name,
                'p_user_id': None,
                'p_jobcode_id': None
            }
        )
        
        # Filter out EVERYTHING tasks
        tasks = [t for t in result if 'EVERYTHING' not in t.get('task_name', '').upper()]
        
        if not tasks:
            return f"❌ No task data for: {job_name}"
        
        # Calculate efficiency for each task
        task_efficiency = []
        
        for task in tasks:
            task_name = task.get('task_name', 'Unknown')
            estimate = task.get('time_estimate', 0)
            actual = task.get('duration_hours', 0)
            
            efficiency = (estimate / actual * 100) if actual > 0 else 0
            
            # Categorize
            if efficiency >= 90:
                category = "Excellent"
                emoji = "🌟"
            elif efficiency >= 75:
                category = "Good"
                emoji = "✅"
            elif efficiency >= 60:
                category = "Fair"
                emoji = "⚠️"
            else:
                category = "Poor"
                emoji = "🔴"
            
            task_efficiency.append({
                'name': task_name,
                'estimate': estimate,
                'actual': actual,
                'efficiency': efficiency,
                'category': category,
                'emoji': emoji
            })
        
        # Sort by efficiency
        sorted_tasks = sorted(task_efficiency, key=lambda x: x['efficiency'], reverse=True)
        
        avg_efficiency = sum(t['efficiency'] for t in task_efficiency) / len(task_efficiency) if task_efficiency else 0
        
        summary = f"""Task Efficiency Summary - {job_name}

Average Efficiency: {avg_efficiency:.1f}%
Total Tasks: {len(tasks)}

Top Efficient Tasks:
"""
        
        for i, task in enumerate(sorted_tasks[:5], 1):
            summary += f"{i}. {task['emoji']} {task['name']}: {task['efficiency']:.1f}% ({task['category']})\n"
        
        summary += "\nLeast Efficient Tasks:\n"
        
        for i, task in enumerate(sorted_tasks[-5:][::-1], 1):
            summary += f"{i}. {task['emoji']} {task['name']}: {task['efficiency']:.1f}% ({task['category']})\n"
        
        return summary
        
    except Exception as e:
        return f"❌ Error calculating efficiency: {str(e)}"

