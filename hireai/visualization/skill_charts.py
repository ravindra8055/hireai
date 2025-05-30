import plotly.graph_objects as go
from plotly.subplots import make_subplots
from typing import List, Dict, Any
from collections import Counter
import pandas as pd
from hireai.database.supabase_client import SupabaseClient

class SkillVisualizer:
    def __init__(self):
        """Initialize the skill visualizer with Supabase client"""
        self.db_client = SupabaseClient()

    def generate_skill_distribution(self, 
                                  top_n: int = 20, 
                                  min_frequency: int = 2,
                                  output_file: str = None) -> go.Figure:
        """
        Generate a bar chart of most common skills from all candidates
        
        Args:
            top_n (int): Number of top skills to display
            min_frequency (int): Minimum frequency to include a skill
            output_file (str): Optional path to save the chart as HTML
            
        Returns:
            go.Figure: Plotly figure object
        """
        # Fetch all candidates
        candidates = self.db_client.get_all_candidates()
        
        # Extract and count skills
        all_skills = []
        for candidate in candidates:
            skills = candidate.get('skills', [])
            if isinstance(skills, list):
                all_skills.extend([skill.lower() for skill in skills])
        
        # Count skill frequencies
        skill_counter = Counter(all_skills)
        
        # Filter by minimum frequency
        filtered_skills = {k: v for k, v in skill_counter.items() if v >= min_frequency}
        
        # Get top N skills
        top_skills = dict(sorted(filtered_skills.items(), 
                               key=lambda x: x[1], 
                               reverse=True)[:top_n])
        
        # Create DataFrame for easier manipulation
        df = pd.DataFrame({
            'Skill': list(top_skills.keys()),
            'Count': list(top_skills.values())
        })
        
        # Create figure
        fig = go.Figure()
        
        # Add bar chart
        fig.add_trace(
            go.Bar(
                x=df['Skill'],
                y=df['Count'],
                text=df['Count'],
                textposition='auto',
                marker_color='rgb(55, 83, 109)',
                hovertemplate="<b>%{x}</b><br>" +
                             "Count: %{y}<br>" +
                             "<extra></extra>"
            )
        )
        
        # Update layout
        fig.update_layout(
            title={
                'text': f'Top {top_n} Most Common Skills',
                'y': 0.95,
                'x': 0.5,
                'xanchor': 'center',
                'yanchor': 'top'
            },
            xaxis_title="Skills",
            yaxis_title="Number of Candidates",
            template="plotly_white",
            showlegend=False,
            height=600,
            margin=dict(t=100, b=100),
            xaxis={'tickangle': 45}
        )
        
        # Save to file if path provided
        if output_file:
            fig.write_html(output_file)
            
        return fig

    def generate_skill_heatmap(self, 
                             top_n: int = 20,
                             min_frequency: int = 2,
                             output_file: str = None) -> go.Figure:
        """
        Generate a heatmap showing skill co-occurrence
        
        Args:
            top_n (int): Number of top skills to include
            min_frequency (int): Minimum frequency to include a skill
            output_file (str): Optional path to save the chart as HTML
            
        Returns:
            go.Figure: Plotly figure object
        """
        # Fetch all candidates
        candidates = self.db_client.get_all_candidates()
        
        # Extract and count skills
        all_skills = []
        for candidate in candidates:
            skills = candidate.get('skills', [])
            if isinstance(skills, list):
                all_skills.extend([skill.lower() for skill in skills])
        
        # Count skill frequencies
        skill_counter = Counter(all_skills)
        
        # Filter by minimum frequency
        filtered_skills = {k: v for k, v in skill_counter.items() if v >= min_frequency}
        
        # Get top N skills
        top_skills = dict(sorted(filtered_skills.items(), 
                               key=lambda x: x[1], 
                               reverse=True)[:top_n])
        
        # Create co-occurrence matrix
        co_occurrence = pd.DataFrame(0, 
                                   index=top_skills.keys(), 
                                   columns=top_skills.keys())
        
        # Fill co-occurrence matrix
        for candidate in candidates:
            skills = candidate.get('skills', [])
            if isinstance(skills, list):
                skills = [skill.lower() for skill in skills]
                for skill1 in skills:
                    for skill2 in skills:
                        if skill1 in co_occurrence.index and skill2 in co_occurrence.columns:
                            co_occurrence.loc[skill1, skill2] += 1
        
        # Create heatmap
        fig = go.Figure(data=go.Heatmap(
            z=co_occurrence.values,
            x=co_occurrence.columns,
            y=co_occurrence.index,
            colorscale='Viridis',
            hovertemplate="<b>%{y}</b> and <b>%{x}</b><br>" +
                         "Co-occurrence: %{z}<br>" +
                         "<extra></extra>"
        ))
        
        # Update layout
        fig.update_layout(
            title={
                'text': 'Skill Co-occurrence Heatmap',
                'y': 0.95,
                'x': 0.5,
                'xanchor': 'center',
                'yanchor': 'top'
            },
            xaxis_title="Skills",
            yaxis_title="Skills",
            template="plotly_white",
            height=800,
            width=1000,
            margin=dict(t=100, b=100, l=100, r=100),
            xaxis={'tickangle': 45},
            yaxis={'tickangle': 0}
        )
        
        # Save to file if path provided
        if output_file:
            fig.write_html(output_file)
            
        return fig

    def generate_skill_trends(self, 
                            time_period: str = 'month',
                            top_n: int = 10,
                            output_file: str = None) -> go.Figure:
        """
        Generate a line chart showing skill trends over time
        
        Args:
            time_period (str): 'day', 'week', 'month', or 'year'
            top_n (int): Number of top skills to track
            output_file (str): Optional path to save the chart as HTML
            
        Returns:
            go.Figure: Plotly figure object
        """
        # Fetch all candidates
        candidates = self.db_client.get_all_candidates()
        
        # Convert to DataFrame
        df = pd.DataFrame(candidates)
        
        # Convert created_at to datetime
        df['created_at'] = pd.to_datetime(df['created_at'])
        
        # Get top N skills overall
        all_skills = []
        for skills in df['skills']:
            if isinstance(skills, list):
                all_skills.extend([skill.lower() for skill in skills])
        
        top_skills = [skill for skill, _ in Counter(all_skills).most_common(top_n)]
        
        # Create time series data
        df['time_period'] = df['created_at'].dt.to_period(time_period[0])
        
        # Count skills over time
        skill_trends = {}
        for skill in top_skills:
            skill_counts = []
            for period in sorted(df['time_period'].unique()):
                period_candidates = df[df['time_period'] == period]
                count = sum(1 for skills in period_candidates['skills'] 
                          if isinstance(skills, list) and skill in [s.lower() for s in skills])
                skill_counts.append(count)
            skill_trends[skill] = skill_counts
        
        # Create figure
        fig = go.Figure()
        
        # Add line for each skill
        for skill, counts in skill_trends.items():
            fig.add_trace(
                go.Scatter(
                    x=sorted(df['time_period'].unique()),
                    y=counts,
                    name=skill,
                    mode='lines+markers',
                    hovertemplate="<b>%{x}</b><br>" +
                                 "Count: %{y}<br>" +
                                 "<extra></extra>"
                )
            )
        
        # Update layout
        fig.update_layout(
            title={
                'text': f'Skill Trends Over Time (Top {top_n} Skills)',
                'y': 0.95,
                'x': 0.5,
                'xanchor': 'center',
                'yanchor': 'top'
            },
            xaxis_title="Time Period",
            yaxis_title="Number of Candidates",
            template="plotly_white",
            height=600,
            margin=dict(t=100, b=100),
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            )
        )
        
        # Save to file if path provided
        if output_file:
            fig.write_html(output_file)
            
        return fig 