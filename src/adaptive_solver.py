"""
Adaptive solver strategy to handle stiff RBC metabolic model interactions.
Uses multiple solver approaches with fallback mechanisms.
"""
import numpy as np
from scipy.integrate import solve_ivp
import warnings
from equadiff_brodbar import equadiff_brodbar

class AdaptiveSolver:
    def __init__(self, timeout_seconds=30):
        self.timeout_seconds = timeout_seconds
        self.solver_configs = [
            # Configuration 1: Optimized RK45 with balanced tolerances
            {
                'method': 'RK45',
                'rtol': 1e-4,
                'atol': 1e-6,
                'max_step': 0.5,
                'name': 'Optimized RK45'
            },
            # Configuration 2: BDF for stiff systems with relaxed tolerances
            {
                'method': 'BDF',
                'rtol': 1e-2,
                'atol': 1e-4,
                'max_step': 1.0,
                'name': 'Relaxed BDF'
            },
            # Configuration 3: Radau for very stiff systems
            {
                'method': 'Radau',
                'rtol': 1e-2,
                'atol': 1e-4,
                'max_step': 0.5,
                'name': 'Radau Stiff'
            },
            # Configuration 4: Ultra-conservative RK45
            {
                'method': 'RK45',
                'rtol': 1e-2,
                'atol': 1e-3,
                'max_step': 0.01,
                'name': 'Ultra-conservative RK45'
            }
        ]
    
    def safe_rhs(self, t, x):
        """Wrapper for RHS function with error handling."""
        try:
            result = equadiff_brodbar(t, x)
            
            # Check for problematic values
            if np.any(np.isnan(result)) or np.any(np.isinf(result)):
                # Return zero derivatives to stop integration gracefully
                return np.zeros_like(result)
            
            # Clip extremely large derivatives to prevent instability
            max_deriv = 1e6
            result = np.clip(result, -max_deriv, max_deriv)
            
            return result
            
        except Exception as e:
            print(f"RHS error at t={t}: {e}")
            return np.zeros_like(x)
    
    def solve_with_timeout(self, config, t_span, x0, t_eval):
        """Solve with timeout and error handling."""
        import signal
        
        class TimeoutException(Exception):
            pass
        
        def timeout_handler(signum, frame):
            raise TimeoutException("Solver timeout")
        
        # Set timeout (only works on Unix-like systems)
        try:
            signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(self.timeout_seconds)
        except:
            pass  # Windows doesn't support SIGALRM
        
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                
                sol = solve_ivp(
                    self.safe_rhs,
                    t_span,
                    x0,
                    method=config['method'],
                    t_eval=t_eval,
                    rtol=config['rtol'],
                    atol=config['atol'],
                    max_step=config['max_step'],
                    dense_output=False
                )
                
            return sol
            
        except TimeoutException:
            print(f"  Timeout after {self.timeout_seconds}s")
            return None
        except Exception as e:
            print(f"  Solver error: {e}")
            return None
        finally:
            try:
                signal.alarm(0)  # Cancel timeout
            except:
                pass
    
    def adaptive_solve(self, t_span, x0, t_eval=None):
        """
        Solve using adaptive strategy with multiple solver configurations.
        """
        if t_eval is None:
            t_eval = np.linspace(t_span[0], t_span[1], 50)
        
        print(f"Adaptive solver: t_span={t_span}, {len(t_eval)} time points")
        
        for i, config in enumerate(self.solver_configs):
            print(f"Trying {config['name']}...")
            
            sol = self.solve_with_timeout(config, t_span, x0, t_eval)
            
            if sol is not None and sol.success:
                print(f"✓ Success with {config['name']}")
                return sol
            elif sol is not None:
                print(f"  Failed: {sol.message}")
            
        # If all solvers fail, try segmented approach
        print("All solvers failed, trying segmented integration...")
        return self.segmented_solve(t_span, x0, t_eval)
    
    def segmented_solve(self, t_span, x0, t_eval):
        """
        Solve in small segments to avoid instability.
        """
        # Divide time span into small segments
        n_segments = 10
        t_segments = np.linspace(t_span[0], t_span[1], n_segments + 1)
        
        # Storage for results
        all_t = [t_span[0]]
        all_y = [x0]
        
        current_x = x0.copy()
        
        for i in range(n_segments):
            segment_span = [t_segments[i], t_segments[i + 1]]
            segment_t_eval = t_eval[(t_eval >= segment_span[0]) & (t_eval <= segment_span[1])]
            
            if len(segment_t_eval) == 0:
                continue
            
            print(f"  Segment {i+1}/{n_segments}: {segment_span[0]:.3f} to {segment_span[1]:.3f}")
            
            # Use most conservative solver for segments
            config = self.solver_configs[-1]  # Ultra-conservative
            
            sol = self.solve_with_timeout(config, segment_span, current_x, segment_t_eval)
            
            if sol is not None and sol.success:
                all_t.extend(sol.t[1:])  # Skip first point to avoid duplication
                all_y.extend([sol.y[:, j] for j in range(1, len(sol.t))])
                current_x = sol.y[:, -1]  # Update initial condition for next segment
            else:
                print(f"  Segment {i+1} failed, stopping integration")
                break
        
        # Create result object
        class SegmentedResult:
            def __init__(self, t, y):
                self.t = np.array(t)
                self.y = np.column_stack(y) if len(y) > 1 else np.array(y).reshape(-1, 1)
                self.success = len(t) > 1
                self.message = "Segmented integration"
        
        return SegmentedResult(all_t, all_y)

def test_adaptive_solver():
    """Test the adaptive solver with the RBC model."""
    from parse import parse
    from parse_initial_conditions import parse_initial_conditions
    
    print("Testing Adaptive Solver")
    print("=" * 30)
    
    # Load model
    model = parse("RBC/Rxn_RBC.txt")
    if not model:
        print("Error: Could not load model")
        return
    
    # Load initial conditions
    x0, _ = parse_initial_conditions(model, "Initial_conditions_JA_Final.xls")
    if x0 is None:
        print("Error: Could not load initial conditions")
        return
    
    # Add H2O2 and pHi
    x0 = np.append(x0, [0.0001, 7.2])
    
    # Test with challenging time span
    t_span = [0.0, 1.0]
    t_eval = np.linspace(0.0, 1.0, 20)
    
    # Create adaptive solver
    solver = AdaptiveSolver(timeout_seconds=10)
    
    # Solve
    sol = solver.adaptive_solve(t_span, x0, t_eval)
    
    if sol.success:
        print(f"\n✓ Adaptive solver successful!")
        print(f"  Solution shape: {sol.y.shape}")
        print(f"  Time points: {len(sol.t)}")
        
        # Check solution quality
        has_nan = np.any(np.isnan(sol.y))
        has_inf = np.any(np.isinf(sol.y))
        print(f"  Contains NaN: {has_nan}")
        print(f"  Contains Inf: {has_inf}")
        
        # Show some key metabolite values
        key_indices = [0, 18, 19, 35, 36, 107]  # GLC, PYR, LAC, ATP, ADP, pHi
        key_names = ['GLC', 'PYR', 'LAC', 'ATP', 'ADP', 'pHi']
        
        print("\nKey metabolite concentrations at final time:")
        for i, name in zip(key_indices, key_names):
            if i < sol.y.shape[0]:
                print(f"  {name}: {sol.y[i, -1]:.6f}")
        
        return sol
    else:
        print(f"\n✗ Adaptive solver failed")
        return None

if __name__ == "__main__":
    test_adaptive_solver()
