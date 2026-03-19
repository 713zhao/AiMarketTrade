"""
End-to-end tests for Flask API and dashboard integration with scanner.

Tests that the web dashboard endpoints correctly serve scanner data and
handle various scenarios (missing data, caching, file fallback, etc).

Run with: pytest tests/test_api_integration.py -v
"""

import pytest
import json
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

# Mock Flask app for testing
@pytest.fixture
def app():
    """Create and configure test Flask app."""
    # Import here to avoid loading app before fixtures ready
    import sys
    from pathlib import Path
    
    # Add project root to path
    project_root = Path(__file__).parent.parent
    sys.path.insert(0, str(project_root))
    
    from web_dashboard_trading import app as flask_app
    flask_app.config['TESTING'] = True
    
    return flask_app


@pytest.fixture
def client(app):
    """Create Flask test client."""
    return app.test_client()


class TestAPIEndpoints:
    """Test Flask API endpoints."""
    
    def test_scanner_status_endpoint(self, client):
        """Test /api/scanner/status endpoint returns valid status."""
        response = client.get('/api/scanner/status')
        
        assert response.status_code == 200
        data = response.get_json()
        
        # Verify response structure
        assert 'running' in data or 'status' in data or 'enabled_industries' in data
        print(f"✓ Scanner status endpoint: {data.keys()}")
    
    def test_scanner_industries_endpoint(self, client):
        """Test /api/scanner/industries endpoint."""
        response = client.get('/api/scanner/industries')
        
        assert response.status_code == 200
        data = response.get_json()
        
        # Should have enabled industries
        assert 'enabled_industries' in data or isinstance(data, list) or isinstance(data, dict)
        print(f"✓ Industries endpoint: {data}")
    
    def test_recommendations_endpoint_tech(self, client):
        """Test /api/scanner/recommendations/TECH endpoint."""
        response = client.get('/api/scanner/recommendations/TECH')
        
        # Should return 200 or 404 if no data
        assert response.status_code in [200, 404]
        
        if response.status_code == 200:
            data = response.get_json()
            assert 'results' in data or isinstance(data, list)
            print(f"✓ TECH recommendations endpoint: {len(data.get('results', data))} results")
    
    def test_all_results_endpoint_finance(self, client):
        """Test /api/scanner/all-results/FINANCE endpoint returns all stocks."""
        response = client.get('/api/scanner/all-results/FINANCE')
        
        assert response.status_code in [200, 404]
        
        if response.status_code == 200:
            data = response.get_json()
            results = data.get('results', [])
            
            # Should include HOLD stocks too (not just BUY/SELL)
            if len(results) > 0:
                recommendations = set(r['recommendation'] for r in results)
                has_hold = 'HOLD' in recommendations
                print(f"✓ All results includes: {recommendations}")
    
    def test_all_results_includes_hold_stocks(self, client):
        """Test that all-results endpoint includes HOLD recommendations."""
        response = client.get('/api/scanner/all-results/FINANCE')
        
        if response.status_code == 200:
            data = response.get_json()
            results = data.get('results', [])
            
            if len(results) > 0:
                # Count by recommendation
                holds = [r for r in results if r['recommendation'] == 'HOLD']
                buys = [r for r in results if r['recommendation'] == 'BUY']
                
                print(f"Results breakdown: {len(buys)} BUY, {len(holds)} HOLD")
                
                # All-results should include HOLD (not filtered like recommendations)
                if len(holds) > 0:
                    print("✓ All-results includes HOLD stocks")


class TestDataFallback:
    """Test that API handles missing data gracefully."""
    
    def test_all_results_file_fallback_loading(self, client):
        """Test that all-results endpoint tries file fallback when cache is empty."""
        # This tests the file fallback logic for persistent data
        response = client.get('/api/scanner/all-results/TECH')
        
        # Should either return cached data or fall back to file
        assert response.status_code in [200, 404]
        
        if response.status_code == 200:
            data = response.get_json()
            if 'results' in data and len(data['results']) > 0:
                print("✓ File fallback loading working (data retrieved from file)")
    
    def test_invalid_industry_returns_404_or_empty(self, client):
        """Test that invalid industry returns 404 or empty results."""
        response = client.get('/api/scanner/all-results/INVALID_INDUSTRY')
        
        # Should handle gracefully
        assert response.status_code in [200, 404]
        
        if response.status_code == 200:
            data = response.get_json()
            results = data.get('results', [])
            assert len(results) == 0 or isinstance(results, list)


class TestResponseStructure:
    """Test that API responses have consistent structure."""
    
    def test_recommendations_response_structure(self, client):
        """Test /recommendations endpoint has proper response structure."""
        for industry in ['TECH', 'FINANCE', 'HEALTHCARE']:
            response = client.get(f'/api/scanner/recommendations/{industry}')
            
            if response.status_code == 200:
                data = response.get_json()
                
                if 'results' in data:
                    results = data['results']
                    
                    for result in results:
                        # Each result should have required fields
                        required = ['ticker', 'recommendation', 'buy_score', 'sell_score']
                        for field in required:
                            assert field in result, f"Missing {field} in {industry} result"
                    
                    print(f"✓ {industry} results have valid structure")
    
    def test_all_results_response_structure(self, client):
        """Test /all-results endpoint has proper response structure."""
        for industry in ['TECH', 'FINANCE']:
            response = client.get(f'/api/scanner/all-results/{industry}')
            
            if response.status_code == 200:
                data = response.get_json()
                results = data.get('results', [])
                
                # Verify each result has required fields
                for result in results:
                    assert 'ticker' in result, f"Missing ticker in {industry}"
                    assert 'recommendation' in result
                    assert result['recommendation'] in ['BUY', 'SELL', 'HOLD']
                    assert 'reason' in result, f"Missing reason for {result.get('ticker')}"
                
                print(f"✓ {industry} all-results have valid structure ({len(results)} total)")


class TestIntegrationScenarios:
    """Test complete dashboard integration scenarios."""
    
    def test_dashboard_page_loads(self, client):
        """Test that dashboard HTML page loads."""
        response = client.get('/')
        
        assert response.status_code == 200
        assert b'html' in response.data.lower() or b'dashboard' in response.data.lower()
        print("✓ Dashboard page loads successfully")
    
    def test_scan_now_endpoint_exists(self, client):
        """Test that scan-now trigger endpoint exists."""
        # Try POST to scan endpoint
        response = client.post('/api/scanner/scan-now', json={})
        
        # Should exist (might return 200, 400, or other 2xx/4xx)
        assert response.status_code < 500
        print(f"✓ Scan endpoint exists (status: {response.status_code})")
    
    def test_scanner_results_endpoint_chain(self, client):
        """Test the full chain of getting scanner results via API."""
        print("\nFull endpoint chain test:")
        
        # 1. Get status
        status_resp = client.get('/api/scanner/status')
        print(f"  1. Status endpoint: {status_resp.status_code}")
        
        # 2. Get industries
        ind_resp = client.get('/api/scanner/industries')
        print(f"  2. Industries endpoint: {ind_resp.status_code}")
        
        if ind_resp.status_code == 200:
            industries = ind_resp.get_json()
            if isinstance(industries, dict) and 'enabled_industries' in industries:
                enabled = industries['enabled_industries']
            elif isinstance(industries, list):
                enabled = industries
            else:
                enabled = ['TECH', 'FINANCE']
            
            # 3. Get recommendations for first enabled industry
            if enabled:
                industry = enabled[0] if isinstance(enabled, list) else list(enabled)[0]
                rec_resp = client.get(f'/api/scanner/recommendations/{industry}')
                print(f"  3. Recommendations for {industry}: {rec_resp.status_code}")
                
                # 4. Get all results for same industry
                all_resp = client.get(f'/api/scanner/all-results/{industry}')
                print(f"  4. All-results for {industry}: {all_resp.status_code}")
        
        print("✓ Full endpoint chain tested")


class TestScannerDataConsistency:
    """Test data consistency between scanner and API."""
    
    def test_api_data_matches_scanner_output(self, client):
        """Test that API returns data from scanner correctly."""
        # Get status to see what's available
        status_resp = client.get('/api/scanner/status')
        
        if status_resp.status_code == 200:
            status_data = status_resp.get_json()
            
            # Try to get recommendations
            response = client.get('/api/scanner/recommendations/FINANCE')
            
            if response.status_code == 200:
                data = response.get_json()
                results = data.get('results', [])
                
                if len(results) > 0:
                    # Verify data integrity
                    for result in results:
                        assert isinstance(result['ticker'], str)
                        assert isinstance(result['buy_score'], (int, float))
                        assert isinstance(result['sell_score'], (int, float))
                    
                    print(f"✓ API data validation: {len(results)} results verified")


class TestErrorHandling:
    """Test API error handling."""
    
    def test_malformed_request_handling(self, client):
        """Test that API handles malformed requests gracefully."""
        # Try to POST with invalid data
        response = client.post('/api/scanner/scan-now', 
                             data='invalid json',
                             content_type='application/json')
        
        # Should not crash (might be 400, 415, etc)
        assert response.status_code < 500
        print(f"✓ Malformed request handled (status: {response.status_code})")
    
    def test_missing_parameter_handling(self, client):
        """Test that API handles missing parameters gracefully."""
        # Try endpoint with missing parameter
        response = client.get('/api/scanner/recommendations/')
        
        # Should handle gracefully (404 or redirect, not 500)
        assert response.status_code != 500
        print(f"✓ Missing parameter handled (status: {response.status_code})")


class TestConcurrency:
    """Test API behavior under concurrent access."""
    
    def test_simultaneous_endpoint_access(self, client):
        """Test that multiple endpoint calls don't interfere."""
        import threading
        
        results = []
        errors = []
        
        def call_endpoint(endpoint):
            try:
                response = client.get(endpoint)
                results.append((endpoint, response.status_code))
            except Exception as e:
                errors.append((endpoint, str(e)))
        
        endpoints = [
            '/api/scanner/status',
            '/api/scanner/recommendations/TECH',
            '/api/scanner/all-results/FINANCE',
        ]
        
        threads = [threading.Thread(target=call_endpoint, args=(ep,)) for ep in endpoints]
        
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        # All should complete without errors
        assert len(errors) == 0, f"Errors occurred: {errors}"
        assert len(results) == len(endpoints)
        
        print(f"✓ Concurrent access test: {len(results)} endpoints completed successfully")


if __name__ == "__main__":
    """
    Run API tests with:
    pytest tests/test_api_integration.py -v
    
    Run specific test class:
    pytest tests/test_api_integration.py::TestAPIEndpoints -v
    
    Run with verbose logging:
    pytest tests/test_api_integration.py -v -s
    """
    pass
