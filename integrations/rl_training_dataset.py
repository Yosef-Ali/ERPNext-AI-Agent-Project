#!/usr/bin/env python3
"""
ERPNext RL Training Dataset Generator
Creates reinforcement learning datasets from ERPNext usage patterns and workflows
"""

import os
import json
import logging
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from collections import defaultdict, Counter
import pickle

from erpnext_connector import ERPNextConnector
from knowledge_graph_builder import ERPNextKnowledgeGraph

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ERPNextRLDatasetGenerator:
    """Generate RL training datasets from ERPNext usage patterns"""
    
    def __init__(self, output_dir: str = "../volumes/rl_datasets"):
        self.output_dir = Path(output_dir).absolute()
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.erpnext = ERPNextConnector()
        self.kg_builder = ERPNextKnowledgeGraph()
        
        # RL dataset structure
        self.datasets = {
            'workflow_optimization': [],
            'document_suggestion': [],
            'field_completion': [],
            'approval_routing': [],
            'error_prevention': []
        }
        
        logger.info(f"RL Dataset Generator initialized, output: {self.output_dir}")
    
    def extract_user_interaction_patterns(self, doctype: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Extract user interaction patterns from ERPNext documents"""
        patterns = []
        
        try:
            # Get sample documents with creation/modification data
            documents = self.erpnext.get_sample_documents(doctype, limit)
            
            for doc in documents:
                if not doc.get('creation') or not doc.get('modified'):
                    continue
                
                pattern = {
                    'doctype': doctype,
                    'name': doc.get('name'),
                    'creation_time': doc.get('creation'),
                    'modified_time': doc.get('modified'),
                    'owner': doc.get('owner'),
                    'modified_by': doc.get('modified_by'),
                    'docstatus': doc.get('docstatus', 0),
                    'status': doc.get('status', 'Unknown')
                }
                
                # Calculate interaction metrics
                pattern['time_to_submit'] = self._calculate_time_diff(
                    doc.get('creation'), doc.get('modified')
                )
                pattern['modification_count'] = 1  # Simplified - would need version history
                pattern['user_changed'] = doc.get('owner') != doc.get('modified_by')
                
                # Extract field completion patterns
                pattern['field_completion'] = self._analyze_field_completion(doc)
                
                # Extract workflow state transitions
                pattern['workflow_transitions'] = self._extract_workflow_transitions(doctype, doc)
                
                patterns.append(pattern)
                
        except Exception as e:
            logger.error(f"Error extracting patterns for {doctype}: {e}")
        
        return patterns
    
    def _calculate_time_diff(self, start_time: str, end_time: str) -> Optional[float]:
        """Calculate time difference in minutes"""
        try:
            from dateutil.parser import parse
            start = parse(start_time)
            end = parse(end_time)
            return (end - start).total_seconds() / 60
        except:
            return None
    
    def _analyze_field_completion(self, doc: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze field completion patterns"""
        completion_stats = {
            'total_fields': 0,
            'completed_fields': 0,
            'completion_rate': 0.0,
            'missing_critical_fields': [],
            'field_types_completed': defaultdict(int)
        }
        
        critical_fields = [
            'customer', 'supplier', 'item_code', 'quantity', 'rate', 'amount',
            'due_date', 'delivery_date', 'project', 'cost_center'
        ]
        
        for field, value in doc.items():
            if field.startswith('_') or field in ['name', 'creation', 'modified']:
                continue
                
            completion_stats['total_fields'] += 1
            
            if value is not None and str(value).strip():
                completion_stats['completed_fields'] += 1
                
                # Categorize field types for analysis
                if field in critical_fields:
                    completion_stats['field_types_completed']['critical'] += 1
                elif 'date' in field.lower():
                    completion_stats['field_types_completed']['date'] += 1
                elif field.endswith('_rate') or field.endswith('_amount'):
                    completion_stats['field_types_completed']['financial'] += 1
                else:
                    completion_stats['field_types_completed']['other'] += 1
            else:
                if field in critical_fields:
                    completion_stats['missing_critical_fields'].append(field)
        
        if completion_stats['total_fields'] > 0:
            completion_stats['completion_rate'] = (
                completion_stats['completed_fields'] / completion_stats['total_fields']
            )
        
        return completion_stats
    
    def _extract_workflow_transitions(self, doctype: str, doc: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract workflow state transitions"""
        transitions = []
        
        # Common ERPNext workflow states
        workflow_states = {
            'Sales Order': ['Draft', 'To Deliver and Bill', 'To Bill', 'To Deliver', 'Completed', 'Cancelled'],
            'Purchase Order': ['Draft', 'To Receive and Bill', 'To Bill', 'To Receive', 'Completed', 'Cancelled'],
            'Sales Invoice': ['Draft', 'Outstanding', 'Paid', 'Cancelled'],
            'Purchase Invoice': ['Draft', 'Outstanding', 'Paid', 'Cancelled']
        }
        
        current_status = doc.get('status', 'Draft')
        docstatus = doc.get('docstatus', 0)
        
        if doctype in workflow_states:
            possible_states = workflow_states[doctype]
            
            transition = {
                'doctype': doctype,
                'current_state': current_status,
                'docstatus': docstatus,
                'possible_next_states': self._get_possible_next_states(current_status, possible_states),
                'completion_score': self._calculate_completion_score(current_status, possible_states)
            }
            
            transitions.append(transition)
        
        return transitions
    
    def _get_possible_next_states(self, current_state: str, possible_states: List[str]) -> List[str]:
        """Get possible next states from current state"""
        try:
            current_index = possible_states.index(current_state)
            # Simplified: next states are usually the ones that follow
            if current_index < len(possible_states) - 1:
                return possible_states[current_index + 1:current_index + 3]  # Next 1-2 states
        except ValueError:
            pass
        
        return []
    
    def _calculate_completion_score(self, current_state: str, possible_states: List[str]) -> float:
        """Calculate workflow completion score (0.0 to 1.0)"""
        try:
            current_index = possible_states.index(current_state)
            return current_index / (len(possible_states) - 1)
        except (ValueError, ZeroDivisionError):
            return 0.0
    
    def generate_workflow_optimization_dataset(self) -> Dict[str, Any]:
        """Generate dataset for workflow optimization RL"""
        logger.info("Generating workflow optimization dataset...")
        
        workflow_data = {
            'states': [],
            'actions': [],
            'rewards': [],
            'next_states': [],
            'metadata': {
                'task_type': 'workflow_optimization',
                'description': 'Optimize document approval and processing workflows'
            }
        }
        
        # Key DocTypes for workflow optimization
        workflow_doctypes = ['Sales Order', 'Purchase Order', 'Sales Invoice', 'Purchase Invoice']
        
        for doctype in workflow_doctypes:
            patterns = self.extract_user_interaction_patterns(doctype, 50)
            
            for pattern in patterns:
                # State: Current document state and completion
                state = {
                    'doctype': doctype,
                    'completion_rate': pattern['field_completion']['completion_rate'],
                    'time_spent': pattern.get('time_to_submit', 0),
                    'missing_critical_fields': len(pattern['field_completion']['missing_critical_fields']),
                    'workflow_stage': pattern['status']
                }
                
                # Action: Workflow transitions taken
                actions = []
                for transition in pattern['workflow_transitions']:
                    actions.extend(transition['possible_next_states'])
                
                # Reward: Based on efficiency and completion
                reward = self._calculate_workflow_reward(pattern)
                
                # Next state: After the workflow action
                next_state = state.copy()
                next_state['workflow_stage'] = pattern['status']  # Simplified
                
                workflow_data['states'].append(state)
                workflow_data['actions'].append(actions)
                workflow_data['rewards'].append(reward)
                workflow_data['next_states'].append(next_state)
        
        self.datasets['workflow_optimization'] = workflow_data
        return workflow_data
    
    def generate_document_suggestion_dataset(self) -> Dict[str, Any]:
        """Generate dataset for document suggestion RL"""
        logger.info("Generating document suggestion dataset...")
        
        suggestion_data = {
            'contexts': [],
            'suggestions': [],
            'acceptance_rates': [],
            'metadata': {
                'task_type': 'document_suggestion',
                'description': 'Suggest relevant documents and fields based on context'
            }
        }
        
        # Analyze document relationships
        doctypes = ['Customer', 'Item', 'Sales Order', 'Purchase Order']
        
        for doctype in doctypes:
            patterns = self.extract_user_interaction_patterns(doctype, 30)
            
            for pattern in patterns:
                # Context: Current document being worked on
                context = {
                    'doctype': doctype,
                    'completed_fields': pattern['field_completion']['completed_fields'],
                    'completion_rate': pattern['field_completion']['completion_rate'],
                    'user': pattern.get('owner', ''),
                    'time_of_day': self._extract_time_features(pattern['creation_time'])
                }
                
                # Suggestions: Related documents or fields that could be helpful
                suggestions = self._generate_document_suggestions(doctype, pattern)
                
                # Acceptance rate: Simulated based on completion patterns
                acceptance_rate = self._simulate_acceptance_rate(pattern)
                
                suggestion_data['contexts'].append(context)
                suggestion_data['suggestions'].append(suggestions)
                suggestion_data['acceptance_rates'].append(acceptance_rate)
        
        self.datasets['document_suggestion'] = suggestion_data
        return suggestion_data
    
    def generate_field_completion_dataset(self) -> Dict[str, Any]:
        """Generate dataset for field completion assistance RL"""
        logger.info("Generating field completion dataset...")
        
        completion_data = {
            'partial_documents': [],
            'suggested_completions': [],
            'completion_success': [],
            'metadata': {
                'task_type': 'field_completion',
                'description': 'Predict and suggest field completions based on partial data'
            }
        }
        
        # Analyze partially completed documents
        doctypes = ['Sales Order', 'Purchase Order', 'Quotation']
        
        for doctype in doctypes:
            patterns = self.extract_user_interaction_patterns(doctype, 40)
            
            for pattern in patterns:
                completion_stats = pattern['field_completion']
                
                if completion_stats['completion_rate'] > 0.3:  # Only partially completed docs
                    # Partial document state
                    partial_doc = {
                        'doctype': doctype,
                        'completion_rate': completion_stats['completion_rate'],
                        'missing_fields': completion_stats['missing_critical_fields'],
                        'completed_field_types': dict(completion_stats['field_types_completed'])
                    }
                    
                    # Suggested completions
                    suggestions = self._generate_field_suggestions(completion_stats)
                    
                    # Success rate (simulated)
                    success_rate = min(1.0, completion_stats['completion_rate'] + 0.2)
                    
                    completion_data['partial_documents'].append(partial_doc)
                    completion_data['suggested_completions'].append(suggestions)
                    completion_data['completion_success'].append(success_rate)
        
        self.datasets['field_completion'] = completion_data
        return completion_data
    
    def _calculate_workflow_reward(self, pattern: Dict[str, Any]) -> float:
        """Calculate reward for workflow efficiency"""
        reward = 0.0
        
        # Reward for high completion rate
        completion_rate = pattern['field_completion']['completion_rate']
        reward += completion_rate * 10
        
        # Penalty for taking too long
        time_spent = pattern.get('time_to_submit', 0)
        if time_spent > 60:  # More than 1 hour
            reward -= 5
        elif time_spent < 10:  # Less than 10 minutes (efficient)
            reward += 5
        
        # Reward for submitting (docstatus = 1)
        if pattern.get('docstatus') == 1:
            reward += 15
        
        # Penalty for missing critical fields
        missing_critical = len(pattern['field_completion']['missing_critical_fields'])
        reward -= missing_critical * 3
        
        return max(0, reward)  # Ensure non-negative reward
    
    def _extract_time_features(self, timestamp: str) -> Dict[str, Any]:
        """Extract time-based features"""
        try:
            from dateutil.parser import parse
            dt = parse(timestamp)
            return {
                'hour': dt.hour,
                'day_of_week': dt.weekday(),
                'is_weekend': dt.weekday() >= 5,
                'is_business_hours': 9 <= dt.hour <= 17
            }
        except:
            return {'hour': 12, 'day_of_week': 1, 'is_weekend': False, 'is_business_hours': True}
    
    def _generate_document_suggestions(self, doctype: str, pattern: Dict[str, Any]) -> List[str]:
        """Generate document suggestions based on context"""
        suggestions = []
        
        # Common document relationships
        if doctype == 'Customer':
            suggestions.extend(['Sales Order', 'Quotation', 'Sales Invoice'])
        elif doctype == 'Item':
            suggestions.extend(['Purchase Order', 'Stock Entry', 'Price List'])
        elif doctype == 'Sales Order':
            suggestions.extend(['Delivery Note', 'Sales Invoice', 'Payment Entry'])
        
        return suggestions[:3]  # Limit to top 3 suggestions
    
    def _simulate_acceptance_rate(self, pattern: Dict[str, Any]) -> float:
        """Simulate suggestion acceptance rate"""
        # Higher completion rate suggests user would accept more suggestions
        base_rate = pattern['field_completion']['completion_rate']
        
        # Add some randomness and factors
        if pattern.get('user_changed', False):
            base_rate *= 0.8  # Lower if multiple users involved
        
        return min(1.0, base_rate + np.random.normal(0, 0.1))
    
    def _generate_field_suggestions(self, completion_stats: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate field completion suggestions"""
        suggestions = []
        
        for missing_field in completion_stats['missing_critical_fields']:
            suggestion = {
                'field_name': missing_field,
                'suggestion_type': 'required',
                'priority': 'high' if missing_field in ['customer', 'item_code', 'quantity'] else 'medium'
            }
            suggestions.append(suggestion)
        
        return suggestions
    
    def export_datasets(self) -> Dict[str, str]:
        """Export all RL datasets to files"""
        exported_files = {}
        
        for dataset_name, dataset in self.datasets.items():
            if dataset:
                # Export as JSON
                json_path = self.output_dir / f"{dataset_name}_dataset.json"
                with open(json_path, 'w') as f:
                    json.dump(dataset, f, indent=2, default=str)
                
                # Export as pickle for ML use
                pickle_path = self.output_dir / f"{dataset_name}_dataset.pkl"
                with open(pickle_path, 'wb') as f:
                    pickle.dump(dataset, f)
                
                exported_files[dataset_name] = str(json_path)
                logger.info(f"Exported {dataset_name} dataset to {json_path}")
        
        return exported_files
    
    def generate_all_datasets(self) -> Dict[str, Any]:
        """Generate all RL training datasets"""
        logger.info("Generating all RL training datasets...")
        
        results = {
            'datasets_generated': [],
            'export_paths': {},
            'statistics': {},
            'connection_status': None
        }
        
        # Test ERPNext connection first
        connection_status = self.erpnext.test_connection()
        results['connection_status'] = connection_status
        
        if not connection_status['connected']:
            logger.warning("ERPNext not connected - generating synthetic datasets")
            # Could generate synthetic data here for testing
            return results
        
        # Generate each dataset
        dataset_generators = [
            ('workflow_optimization', self.generate_workflow_optimization_dataset),
            ('document_suggestion', self.generate_document_suggestion_dataset),
            ('field_completion', self.generate_field_completion_dataset)
        ]
        
        for dataset_name, generator_func in dataset_generators:
            try:
                dataset = generator_func()
                if dataset:
                    results['datasets_generated'].append(dataset_name)
                    
                    # Calculate statistics
                    if isinstance(dataset, dict) and 'states' in dataset:
                        results['statistics'][dataset_name] = {
                            'samples': len(dataset['states']),
                            'avg_reward': np.mean(dataset.get('rewards', [0])) if dataset.get('rewards') else 0
                        }
                    elif isinstance(dataset, dict) and 'contexts' in dataset:
                        results['statistics'][dataset_name] = {
                            'samples': len(dataset['contexts']),
                            'avg_acceptance_rate': np.mean(dataset.get('acceptance_rates', [0])) if dataset.get('acceptance_rates') else 0
                        }
                    
            except Exception as e:
                logger.error(f"Error generating {dataset_name} dataset: {e}")
        
        # Export all datasets
        results['export_paths'] = self.export_datasets()
        
        return results

def main():
    """Generate RL training datasets"""
    generator = ERPNextRLDatasetGenerator()
    
    print("🤖 Generating RL Training Datasets...")
    
    results = generator.generate_all_datasets()
    
    print(f"Connection Status: {'✅' if results['connection_status']['connected'] else '❌'}")
    print(f"Datasets Generated: {len(results['datasets_generated'])}")
    
    for dataset_name in results['datasets_generated']:
        stats = results['statistics'].get(dataset_name, {})
        print(f"  📊 {dataset_name}: {stats.get('samples', 0)} samples")
    
    print(f"\nExported Files:")
    for dataset_name, path in results['export_paths'].items():
        print(f"  📁 {dataset_name}: {path}")

if __name__ == "__main__":
    main()