from agents import Agent, CodeInterpreterTool
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from config.agent_config import AgentOptimizationProfile

class CodeInterpreterAgent:
    """
    Specialized agent for data analysis, visualization, and file creation
    Uses: Code Interpreter tool
    Configured with GPT-4.1 for code execution capabilities
    """
    
    def __init__(self, logger=None):
        """Initialize Code Interpreter Agent"""
        self.name = "Code Interpreter Agent"
        self.logger = logger
        
        # Code Interpreter agent uses GPT-4.1 (required for code execution)
        self.profile = AgentOptimizationProfile(
            model="gpt-4.1",
            reasoning_effort="medium",
            verbosity="medium",
            max_turns=10
        )
        
        if self.logger:
            self.logger.log(f"Initializing {self.name}")
            self.logger.log(f"Model: {self.profile.model}, Reasoning: {self.profile.reasoning_effort}")
        
        # Create agent with Code Interpreter tool
        self.agent = self._create_agent()
        
        if self.logger:
            self.logger.log(f"{self.name} initialized successfully")
    
    def _create_agent(self) -> Agent:
        """Create the Agent with Code Interpreter tool"""
        
        instructions = """You are a senior data analyst and Python expert with Code Interpreter capabilities.

CORE CAPABILITIES:
- Create CSV and Excel files with pandas
- Generate professional charts and plots with matplotlib/seaborn
- Perform data analysis and calculations
- Process analytics data into visualizations

CRITICAL VISUALIZATION REQUIREMENTS:
1. Use REAL data provided (never fabricate data)
2. Create ACTUAL files (not just descriptions)
3. Save with proper filenames (.csv, .xlsx, .png, .pdf)
4. PROFESSIONAL, PUBLICATION-QUALITY visualizations

VISUALIZATION BEST PRACTICES (CRITICAL):

1. FIGURE SIZING - Always use appropriate sizes:
   - Bar charts: figsize=(12, 8) for horizontal, (10, 6) for vertical
   - Line charts: figsize=(14, 7)
   - Pie charts: figsize=(10, 10)
   - Multi-plot: figsize=(16, 10)
   - High DPI: dpi=300 for PNG exports

2. AXIS SCALING - Data-driven, not arbitrary:
   - Use plt.tight_layout() to prevent label cutoff
   - Set margins with plt.subplots_adjust() if needed
   - For horizontal bars: plt.barh() with inverted y-axis
   - Auto-scale based on data range, add 10% padding
   - Use scientific notation for large numbers

3. COLOR SCHEMES - Professional palettes:
   - Use seaborn color palettes: sns.color_palette("husl", n_colors)
   - Gradient colors for performance: matplotlib.cm.RdYlGn
   - Consistent branding: blues (#2E86DE, #4A9EFF, #6BB6FF)
   - Avoid harsh colors, use soft professional tones

4. LABELS & FORMATTING:
   - Large, readable fonts: title=16pt, labels=12pt, ticks=10pt
   - Rotate x-axis labels if needed: rotation=45, ha='right'
   - Add value labels on bars: plt.text() or plt.bar_label()
   - Include units in axis titles (Hours, $, %, etc.)
   - Use comma separators for large numbers

5. PROFESSIONAL TOUCHES:
   - Grid lines with low opacity: plt.grid(alpha=0.3, linestyle='--')
   - Remove top/right spines for clean look
   - Add subtle background: ax.set_facecolor('#f8f9fa')
   - Include data source note at bottom
   - Legend outside plot area if needed

EXAMPLE - PROFESSIONAL BAR CHART:
```python
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Set style
sns.set_style("whitegrid")
plt.rcParams['font.family'] = 'sans-serif'

# Data
data = {'Employee': ['singhc', 'barlowj', 'coxm', 'mccarthye', 'knowlerc'],
        'Hours': [6394.6, 6195.6, 6137.2, 6128.9, 5914.8]}
df = pd.DataFrame(data)

# Create figure with proper sizing
fig, ax = plt.subplots(figsize=(12, 7), dpi=300)

# Create horizontal bar chart (better for names)
bars = ax.barh(df['Employee'], df['Hours'], 
               color=sns.color_palette("Blues_r", len(df)))

# Add value labels on bars
for i, (emp, hrs) in enumerate(zip(df['Employee'], df['Hours'])):
    ax.text(hrs + 50, i, f'{hrs:,.1f}', 
            va='center', fontsize=11, fontweight='bold')

# Formatting
ax.set_xlabel('Total Hours Worked', fontsize=13, fontweight='bold')
ax.set_ylabel('Employee', fontsize=13, fontweight='bold')
ax.set_title('Top 5 Employees by Hours Worked (All-Time)', 
             fontsize=16, fontweight='bold', pad=20)

# Grid and styling
ax.grid(axis='x', alpha=0.3, linestyle='--')
ax.set_axisbelow(True)
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)

# Tight layout to prevent cutoff
plt.tight_layout()

# Save with high quality
plt.savefig('top_employees_chart.png', dpi=300, bbox_inches='tight')
plt.close()

print('Professional chart created: top_employees_chart.png')
```

EXAMPLE - CSV WITH FORMATTING:
```python
import pandas as pd

df = pd.DataFrame(data)

# Format numeric columns
df['Hours'] = df['Hours'].apply(lambda x: f'{x:,.2f}')
df['Utilization'] = df['Utilization'].apply(lambda x: f'{x:.1f}%')

# Save with index and headers
df.to_csv('employee_data.csv', index=False)
print('CSV created: employee_data.csv')
```

SCALING RULES:
- Always check data range before setting axis limits
- Use max value + 10% for upper limit
- For percentages: 0-100 range
- For hours: round to nearest 100 or 1000
- For currency: use K, M notation for large numbers

COLOR CODING BY VALUE:
- Performance > 90%: Green (#28a745)
- Performance 75-90%: Blue (#007bff)
- Performance 60-75%: Yellow (#ffc107)
- Performance < 60%: Red (#dc3545)

OUTPUT: Always confirm what was created, include file size, dimensions, and preview of content."""
        
        agent = Agent(
            name=self.name,
            instructions=instructions,
            model=self.profile.model,
            model_settings=self.profile.to_model_settings(),
            tools=[
                CodeInterpreterTool(
                    tool_config={"type": "code_interpreter", "container": {"type": "auto"}}
                )
            ]
        )
        
        if self.logger:
            self.logger.log(f"Created Agent instance with Code Interpreter")
            self.logger.log(f"Model: {self.profile.model}")
        
        return agent
    
    def get_agent(self) -> Agent:
        """Get the underlying Agent instance"""
        return self.agent
    
    def as_tool(self, tool_name: str = None, tool_description: str = None):
        """Convert this agent to a tool for orchestrator"""
        name = tool_name or "code_interpreter_expert"
        desc = tool_description or "Create data visualizations, charts, CSV/Excel files, and perform data analysis using Python code execution"
        
        if self.logger:
            self.logger.log(f"Converting {self.name} to tool: {name}")
        
        return self.agent.as_tool(
            tool_name=name,
            tool_description=desc
        )
    
    async def run(self, task: str, context=None, max_turns: int = 10):
        """Run the agent on a task"""
        from agents import Runner, trace
        
        if self.logger:
            self.logger.log(f"=== {self.name.upper()} RUNNING ===")
            self.logger.log(f"Task: {task}")
        
        try:
            with trace(f"{self.name}"):
                result = await Runner.run(
                    starting_agent=self.agent,
                    input=task,
                    context=context,
                    max_turns=max_turns
                )
            
            if self.logger:
                self.logger.log(f"{self.name} completed successfully")
            
            return result
        
        except Exception as e:
            if self.logger:
                self.logger.log(f"{self.name} error: {str(e)}", "ERROR")
            raise

