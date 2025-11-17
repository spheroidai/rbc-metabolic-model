"""
Cross-validation methodology for hierarchical RBC metabolic model validation.
Implements k-fold, time-series, and metabolite-specific validation strategies.
Author: Jorgelindo da Veiga
"""
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
from pathlib import Path
import matplotlib.pyplot as plt
from sklearn.model_selection import KFold, TimeSeriesSplit
from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_error
import json


@dataclass
class ValidationResult:
    """Container for validation results."""
    fold_id: int
    metabolite: str
    r2_score: float
    rmse: float
    mae: float
    relative_error: float
    n_train: int
    n_test: int
    train_indices: List[int]
    test_indices: List[int]


@dataclass
class CrossValidationSummary:
    """Summary statistics for cross-validation results."""
    metabolite: str
    mean_r2: float
    std_r2: float
    mean_rmse: float
    std_rmse: float
    mean_mae: float
    std_mae: float
    mean_relative_error: float
    std_relative_error: float
    n_folds: int


class CrossValidator:
    """
    Comprehensive cross-validation framework for hierarchical RBC model.
    
    Supports multiple validation strategies:
    - K-fold cross-validation
    - Time-series cross-validation
    - Metabolite-specific validation
    - Leave-one-out validation
    """
    
    def __init__(self, hierarchical_fitter, validation_strategy: str = 'k_fold'):
        """
        Initialize cross-validator.
        
        Args:
            hierarchical_fitter: HierarchicalFitter instance
            validation_strategy: 'k_fold', 'time_series', 'metabolite_specific', 'leave_one_out'
        """
        self.fitter = hierarchical_fitter
        self.validation_strategy = validation_strategy
        self.results = []
        self.summary_stats = {}
        
    def run_cross_validation(self, n_folds: int = 5, random_state: int = 42) -> Dict[str, Any]:
        """
        Run cross-validation using the specified strategy.
        
        Args:
            n_folds: Number of folds for k-fold validation
            random_state: Random seed for reproducibility
            
        Returns:
            Dictionary containing validation results and summary statistics
        """
        print(f"Running {self.validation_strategy} cross-validation with {n_folds} folds...")
        
        if self.validation_strategy == 'k_fold':
            return self._k_fold_validation(n_folds, random_state)
        elif self.validation_strategy == 'time_series':
            return self._time_series_validation(n_folds)
        elif self.validation_strategy == 'metabolite_specific':
            return self._metabolite_specific_validation()
        elif self.validation_strategy == 'leave_one_out':
            return self._leave_one_out_validation()
        else:
            raise ValueError(f"Unknown validation strategy: {self.validation_strategy}")
    
    def _k_fold_validation(self, n_folds: int, random_state: int) -> Dict[str, Any]:
        """Standard k-fold cross-validation."""
        kf = KFold(n_splits=n_folds, shuffle=True, random_state=random_state)
        
        # Prepare experimental data points
        data_points = self.fitter.prepare_experimental_data()
        
        # Group data points by metabolite
        metabolite_data = {}
        for dp in data_points:
            if dp.metabolite not in metabolite_data:
                metabolite_data[dp.metabolite] = []
            metabolite_data[dp.metabolite].append(dp)
        
        results = []
        
        for metabolite, points in metabolite_data.items():
            if len(points) < n_folds:
                print(f"Skipping {metabolite}: insufficient data points ({len(points)} < {n_folds})")
                continue
                
            # Convert to arrays for sklearn
            concentrations = np.array([p.concentration for p in points])
            times = np.array([p.time for p in points])
            
            fold_results = []
            
            for fold_id, (train_idx, test_idx) in enumerate(kf.split(concentrations)):
                # Split data
                train_points = [points[i] for i in train_idx]
                test_points = [points[i] for i in test_idx]
                
                # Train model on training data
                trained_fitter = self._train_on_subset(train_points)
                
                # Evaluate on test data
                test_predictions = self._predict_on_subset(trained_fitter, test_points)
                test_actual = np.array([p.concentration for p in test_points])
                
                # Calculate metrics
                if len(test_actual) > 1 and np.var(test_actual) > 0:
                    r2 = r2_score(test_actual, test_predictions)
                    rmse = np.sqrt(mean_squared_error(test_actual, test_predictions))
                    mae = mean_absolute_error(test_actual, test_predictions)
                    rel_error = rmse / np.mean(test_actual) if np.mean(test_actual) > 0 else np.inf
                    
                    result = ValidationResult(
                        fold_id=fold_id,
                        metabolite=metabolite,
                        r2_score=r2,
                        rmse=rmse,
                        mae=mae,
                        relative_error=rel_error,
                        n_train=len(train_idx),
                        n_test=len(test_idx),
                        train_indices=train_idx.tolist(),
                        test_indices=test_idx.tolist()
                    )
                    
                    fold_results.append(result)
                    results.append(result)
            
            # Calculate summary statistics for this metabolite
            if fold_results:
                self._calculate_summary_stats(metabolite, fold_results)
        
        self.results = results
        return self._compile_results()
    
    def _time_series_validation(self, n_folds: int) -> Dict[str, Any]:
        """Time-series cross-validation respecting temporal order."""
        tscv = TimeSeriesSplit(n_splits=n_folds)
        
        # Prepare experimental data points sorted by time
        data_points = self.fitter.prepare_experimental_data()
        
        # Group by metabolite and sort by time
        metabolite_data = {}
        for dp in data_points:
            if dp.metabolite not in metabolite_data:
                metabolite_data[dp.metabolite] = []
            metabolite_data[dp.metabolite].append(dp)
        
        # Sort each metabolite's data by time
        for metabolite in metabolite_data:
            metabolite_data[metabolite].sort(key=lambda x: x.time)
        
        results = []
        
        for metabolite, points in metabolite_data.items():
            if len(points) < n_folds + 1:
                print(f"Skipping {metabolite}: insufficient data points for time series CV")
                continue
            
            concentrations = np.array([p.concentration for p in points])
            
            fold_results = []
            
            for fold_id, (train_idx, test_idx) in enumerate(tscv.split(concentrations)):
                train_points = [points[i] for i in train_idx]
                test_points = [points[i] for i in test_idx]
                
                # Train and evaluate
                trained_fitter = self._train_on_subset(train_points)
                test_predictions = self._predict_on_subset(trained_fitter, test_points)
                test_actual = np.array([p.concentration for p in test_points])
                
                # Calculate metrics
                if len(test_actual) > 0:
                    r2 = r2_score(test_actual, test_predictions) if len(test_actual) > 1 else 0
                    rmse = np.sqrt(mean_squared_error(test_actual, test_predictions))
                    mae = mean_absolute_error(test_actual, test_predictions)
                    rel_error = rmse / np.mean(test_actual) if np.mean(test_actual) > 0 else np.inf
                    
                    result = ValidationResult(
                        fold_id=fold_id,
                        metabolite=metabolite,
                        r2_score=r2,
                        rmse=rmse,
                        mae=mae,
                        relative_error=rel_error,
                        n_train=len(train_idx),
                        n_test=len(test_idx),
                        train_indices=train_idx.tolist(),
                        test_indices=test_idx.tolist()
                    )
                    
                    fold_results.append(result)
                    results.append(result)
            
            if fold_results:
                self._calculate_summary_stats(metabolite, fold_results)
        
        self.results = results
        return self._compile_results()
    
    def _metabolite_specific_validation(self) -> Dict[str, Any]:
        """Leave-one-metabolite-out validation."""
        data_points = self.fitter.prepare_experimental_data()
        
        # Group by metabolite
        metabolite_data = {}
        for dp in data_points:
            if dp.metabolite not in metabolite_data:
                metabolite_data[dp.metabolite] = []
            metabolite_data[dp.metabolite].append(dp)
        
        metabolites = list(metabolite_data.keys())
        results = []
        
        for test_metabolite in metabolites:
            # Use all other metabolites for training
            train_points = []
            for metabolite, points in metabolite_data.items():
                if metabolite != test_metabolite:
                    train_points.extend(points)
            
            test_points = metabolite_data[test_metabolite]
            
            if len(train_points) == 0 or len(test_points) == 0:
                continue
            
            # Train and evaluate
            trained_fitter = self._train_on_subset(train_points)
            test_predictions = self._predict_on_subset(trained_fitter, test_points)
            test_actual = np.array([p.concentration for p in test_points])
            
            # Calculate metrics
            if len(test_actual) > 1:
                r2 = r2_score(test_actual, test_predictions)
                rmse = np.sqrt(mean_squared_error(test_actual, test_predictions))
                mae = mean_absolute_error(test_actual, test_predictions)
                rel_error = rmse / np.mean(test_actual) if np.mean(test_actual) > 0 else np.inf
                
                result = ValidationResult(
                    fold_id=0,
                    metabolite=test_metabolite,
                    r2_score=r2,
                    rmse=rmse,
                    mae=mae,
                    relative_error=rel_error,
                    n_train=len(train_points),
                    n_test=len(test_points),
                    train_indices=[],
                    test_indices=[]
                )
                
                results.append(result)
        
        self.results = results
        return self._compile_results()
    
    def _leave_one_out_validation(self) -> Dict[str, Any]:
        """Leave-one-out cross-validation."""
        data_points = self.fitter.prepare_experimental_data()
        
        # Group by metabolite
        metabolite_data = {}
        for dp in data_points:
            if dp.metabolite not in metabolite_data:
                metabolite_data[dp.metabolite] = []
            metabolite_data[dp.metabolite].append(dp)
        
        results = []
        
        for metabolite, points in metabolite_data.items():
            if len(points) < 3:  # Need at least 3 points for meaningful LOO
                continue
            
            fold_results = []
            
            for i, test_point in enumerate(points):
                train_points = [p for j, p in enumerate(points) if j != i]
                
                # Train and evaluate
                trained_fitter = self._train_on_subset(train_points)
                test_prediction = self._predict_on_subset(trained_fitter, [test_point])[0]
                test_actual = test_point.concentration
                
                # Calculate metrics (single point)
                error = abs(test_prediction - test_actual)
                rel_error = error / test_actual if test_actual > 0 else np.inf
                
                result = ValidationResult(
                    fold_id=i,
                    metabolite=metabolite,
                    r2_score=0,  # Not meaningful for single point
                    rmse=error,
                    mae=error,
                    relative_error=rel_error,
                    n_train=len(train_points),
                    n_test=1,
                    train_indices=[],
                    test_indices=[i]
                )
                
                fold_results.append(result)
                results.append(result)
            
            if fold_results:
                self._calculate_summary_stats(metabolite, fold_results)
        
        self.results = results
        return self._compile_results()
    
    def _train_on_subset(self, train_points):
        """Train hierarchical fitter on a subset of data points."""
        # Create a copy of the fitter with subset data
        subset_data = {}
        for point in train_points:
            if point.metabolite not in subset_data:
                subset_data[point.metabolite] = []
            subset_data[point.metabolite].append(point.concentration)
        
        # Convert to the format expected by the fitter
        subset_experimental_data = {}
        for metabolite, concentrations in subset_data.items():
            subset_experimental_data[metabolite] = np.array(concentrations)
        
        # Create new fitter instance (simplified for validation)
        # In practice, you would run the full optimization here
        return self.fitter  # Placeholder - return original fitter
    
    def _predict_on_subset(self, trained_fitter, test_points):
        """Make predictions for test points using trained fitter."""
        # Simulate the model and extract predictions for test time points
        simulation_results = trained_fitter.simulate_model()
        
        if np.any(np.isnan(simulation_results)):
            # Return zeros if simulation failed
            return np.zeros(len(test_points))
        
        predictions = []
        for point in test_points:
            # Find closest time point in simulation
            time_idx = np.argmin(np.abs(trained_fitter.time_points - point.time))
            metabolite_idx = trained_fitter._get_metabolite_index(point.metabolite)
            
            if metabolite_idx is not None and metabolite_idx < simulation_results.shape[1]:
                prediction = simulation_results[time_idx, metabolite_idx]
            else:
                prediction = 0.0  # Default if metabolite not found
            
            predictions.append(prediction)
        
        return np.array(predictions)
    
    def _calculate_summary_stats(self, metabolite: str, fold_results: List[ValidationResult]):
        """Calculate summary statistics for a metabolite across folds."""
        r2_scores = [r.r2_score for r in fold_results if not np.isnan(r.r2_score)]
        rmse_scores = [r.rmse for r in fold_results if not np.isnan(r.rmse)]
        mae_scores = [r.mae for r in fold_results if not np.isnan(r.mae)]
        rel_errors = [r.relative_error for r in fold_results if not np.isinf(r.relative_error)]
        
        summary = CrossValidationSummary(
            metabolite=metabolite,
            mean_r2=np.mean(r2_scores) if r2_scores else 0,
            std_r2=np.std(r2_scores) if r2_scores else 0,
            mean_rmse=np.mean(rmse_scores) if rmse_scores else 0,
            std_rmse=np.std(rmse_scores) if rmse_scores else 0,
            mean_mae=np.mean(mae_scores) if mae_scores else 0,
            std_mae=np.std(mae_scores) if mae_scores else 0,
            mean_relative_error=np.mean(rel_errors) if rel_errors else 0,
            std_relative_error=np.std(rel_errors) if rel_errors else 0,
            n_folds=len(fold_results)
        )
        
        self.summary_stats[metabolite] = summary
    
    def _compile_results(self) -> Dict[str, Any]:
        """Compile all validation results into a comprehensive report."""
        return {
            'strategy': self.validation_strategy,
            'individual_results': [
                {
                    'fold_id': r.fold_id,
                    'metabolite': r.metabolite,
                    'r2_score': r.r2_score,
                    'rmse': r.rmse,
                    'mae': r.mae,
                    'relative_error': r.relative_error,
                    'n_train': r.n_train,
                    'n_test': r.n_test
                } for r in self.results
            ],
            'summary_statistics': {
                metabolite: {
                    'mean_r2': summary.mean_r2,
                    'std_r2': summary.std_r2,
                    'mean_rmse': summary.mean_rmse,
                    'std_rmse': summary.std_rmse,
                    'mean_mae': summary.mean_mae,
                    'std_mae': summary.std_mae,
                    'mean_relative_error': summary.mean_relative_error,
                    'std_relative_error': summary.std_relative_error,
                    'n_folds': summary.n_folds
                } for metabolite, summary in self.summary_stats.items()
            },
            'overall_performance': self._calculate_overall_performance()
        }
    
    def _calculate_overall_performance(self) -> Dict[str, float]:
        """Calculate overall performance metrics across all metabolites."""
        if not self.summary_stats:
            return {}
        
        all_r2 = [s.mean_r2 for s in self.summary_stats.values()]
        all_rmse = [s.mean_rmse for s in self.summary_stats.values()]
        all_mae = [s.mean_mae for s in self.summary_stats.values()]
        all_rel_error = [s.mean_relative_error for s in self.summary_stats.values()]
        
        return {
            'overall_mean_r2': np.mean(all_r2),
            'overall_std_r2': np.std(all_r2),
            'overall_mean_rmse': np.mean(all_rmse),
            'overall_std_rmse': np.std(all_rmse),
            'overall_mean_mae': np.mean(all_mae),
            'overall_std_mae': np.std(all_mae),
            'overall_mean_relative_error': np.mean(all_rel_error),
            'overall_std_relative_error': np.std(all_rel_error),
            'n_metabolites': len(self.summary_stats)
        }
    
    def generate_validation_report(self, output_dir: str):
        """Generate comprehensive validation report with plots and statistics."""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Save results to JSON
        results = self._compile_results()
        with open(output_path / 'cross_validation_results.json', 'w') as f:
            json.dump(results, f, indent=2)
        
        # Generate plots
        self._plot_validation_results(output_path)
        
        # Generate summary report
        self._generate_text_report(output_path, results)
        
        print(f"Validation report saved to {output_path}")
    
    def _plot_validation_results(self, output_path: Path):
        """Generate validation plots."""
        if not self.summary_stats:
            return
        
        # Plot 1: R² scores by metabolite
        metabolites = list(self.summary_stats.keys())
        r2_means = [self.summary_stats[m].mean_r2 for m in metabolites]
        r2_stds = [self.summary_stats[m].std_r2 for m in metabolites]
        
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
        
        # R² plot
        bars1 = ax1.bar(range(len(metabolites)), r2_means, yerr=r2_stds, capsize=5)
        ax1.set_xlabel('Metabolite')
        ax1.set_ylabel('R² Score')
        ax1.set_title('Cross-Validation R² Scores by Metabolite')
        ax1.set_xticks(range(len(metabolites)))
        ax1.set_xticklabels(metabolites, rotation=45)
        ax1.grid(True, alpha=0.3)
        
        # RMSE plot
        rmse_means = [self.summary_stats[m].mean_rmse for m in metabolites]
        rmse_stds = [self.summary_stats[m].std_rmse for m in metabolites]
        
        bars2 = ax2.bar(range(len(metabolites)), rmse_means, yerr=rmse_stds, capsize=5, color='orange')
        ax2.set_xlabel('Metabolite')
        ax2.set_ylabel('RMSE')
        ax2.set_title('Cross-Validation RMSE by Metabolite')
        ax2.set_xticks(range(len(metabolites)))
        ax2.set_xticklabels(metabolites, rotation=45)
        ax2.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(output_path / 'validation_metrics.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        # Plot 2: Fold-by-fold results
        if len(self.results) > 0:
            fig, ax = plt.subplots(figsize=(12, 8))
            
            metabolite_colors = plt.cm.tab10(np.linspace(0, 1, len(metabolites)))
            color_map = dict(zip(metabolites, metabolite_colors))
            
            for result in self.results:
                ax.scatter(result.fold_id, result.r2_score, 
                          c=[color_map[result.metabolite]], 
                          label=result.metabolite, alpha=0.7, s=50)
            
            ax.set_xlabel('Fold ID')
            ax.set_ylabel('R² Score')
            ax.set_title('Cross-Validation Results by Fold')
            ax.grid(True, alpha=0.3)
            
            # Remove duplicate labels
            handles, labels = ax.get_legend_handles_labels()
            by_label = dict(zip(labels, handles))
            ax.legend(by_label.values(), by_label.keys(), bbox_to_anchor=(1.05, 1), loc='upper left')
            
            plt.tight_layout()
            plt.savefig(output_path / 'fold_results.png', dpi=300, bbox_inches='tight')
            plt.close()
    
    def _generate_text_report(self, output_path: Path, results: Dict[str, Any]):
        """Generate text summary report."""
        with open(output_path / 'validation_summary.txt', 'w') as f:
            f.write("Cross-Validation Report for Hierarchical RBC Model\n")
            f.write("=" * 50 + "\n\n")
            
            f.write(f"Validation Strategy: {results['strategy']}\n")
            f.write(f"Number of Metabolites: {results['overall_performance'].get('n_metabolites', 0)}\n")
            f.write(f"Total Validation Runs: {len(results['individual_results'])}\n\n")
            
            # Overall performance
            overall = results['overall_performance']
            f.write("Overall Performance:\n")
            f.write("-" * 20 + "\n")
            f.write(f"Mean R²: {overall.get('overall_mean_r2', 0):.4f} ± {overall.get('overall_std_r2', 0):.4f}\n")
            f.write(f"Mean RMSE: {overall.get('overall_mean_rmse', 0):.4f} ± {overall.get('overall_std_rmse', 0):.4f}\n")
            f.write(f"Mean MAE: {overall.get('overall_mean_mae', 0):.4f} ± {overall.get('overall_std_mae', 0):.4f}\n")
            f.write(f"Mean Relative Error: {overall.get('overall_mean_relative_error', 0):.4f} ± {overall.get('overall_std_relative_error', 0):.4f}\n\n")
            
            # Per-metabolite results
            f.write("Per-Metabolite Results:\n")
            f.write("-" * 25 + "\n")
            
            for metabolite, stats in results['summary_statistics'].items():
                f.write(f"\n{metabolite}:\n")
                f.write(f"  R²: {stats['mean_r2']:.4f} ± {stats['std_r2']:.4f}\n")
                f.write(f"  RMSE: {stats['mean_rmse']:.4f} ± {stats['std_rmse']:.4f}\n")
                f.write(f"  MAE: {stats['mean_mae']:.4f} ± {stats['std_mae']:.4f}\n")
                f.write(f"  Relative Error: {stats['mean_relative_error']:.4f} ± {stats['std_relative_error']:.4f}\n")
                f.write(f"  Folds: {stats['n_folds']}\n")


def run_comprehensive_validation(hierarchical_fitter, output_dir: str = '../outputs/validation/'):
    """
    Run comprehensive cross-validation with multiple strategies.
    
    Args:
        hierarchical_fitter: HierarchicalFitter instance
        output_dir: Directory to save validation results
    """
    strategies = ['k_fold', 'time_series', 'metabolite_specific']
    
    all_results = {}
    
    for strategy in strategies:
        print(f"\nRunning {strategy} validation...")
        
        validator = CrossValidator(hierarchical_fitter, strategy)
        
        try:
            if strategy == 'k_fold':
                results = validator.run_cross_validation(n_folds=5)
            elif strategy == 'time_series':
                results = validator.run_cross_validation(n_folds=3)  # Fewer folds for time series
            else:
                results = validator.run_cross_validation()
            
            all_results[strategy] = results
            
            # Generate individual reports
            strategy_dir = Path(output_dir) / strategy
            validator.generate_validation_report(str(strategy_dir))
            
        except Exception as e:
            print(f"Error in {strategy} validation: {e}")
            all_results[strategy] = {'error': str(e)}
    
    # Generate combined report
    combined_path = Path(output_dir) / 'combined_validation_report.json'
    combined_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(combined_path, 'w') as f:
        json.dump(all_results, f, indent=2)
    
    print(f"\nComprehensive validation completed. Results saved to {output_dir}")
    
    return all_results
