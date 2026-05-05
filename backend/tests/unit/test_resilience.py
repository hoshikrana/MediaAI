import pytest
import asyncio
from unittest.mock import AsyncMock
from backend.orchestration.resilience import (
    retry, RetryConfig, CircuitBreaker, CircuitBreakerConfig, CircuitState
)
from backend.core.exceptions import InferenceError, ValidationError, CircuitOpenError

@pytest.mark.asyncio
async def test_retry_succeeds_on_third_attempt():
    mock_func = AsyncMock(side_effect=[InferenceError(), InferenceError(), "success"])
    decorated = retry(RetryConfig(max_attempts=3, initial_delay_seconds=0.01))(mock_func)
    
    result = await decorated()
    assert result == "success"
    assert mock_func.call_count == 3

@pytest.mark.asyncio
async def test_retry_raises_after_max_attempts():
    mock_func = AsyncMock(side_effect=InferenceError())
    decorated = retry(RetryConfig(max_attempts=2, initial_delay_seconds=0.01))(mock_func)
    
    with pytest.raises(InferenceError):
        await decorated()
    assert mock_func.call_count == 2

@pytest.mark.asyncio
async def test_no_retry_on_excluded_exceptions():
    mock_func = AsyncMock(side_effect=ValidationError())
    decorated = retry(RetryConfig())(mock_func)
    
    with pytest.raises(ValidationError):
        await decorated()
    assert mock_func.call_count == 1 # Failed immediately, no retry

@pytest.mark.asyncio
async def test_circuit_opens_after_threshold():
    cb = CircuitBreaker(CircuitBreakerConfig("test", failure_threshold=2, timeout_seconds=60))
    mock_fail = AsyncMock(side_effect=InferenceError())
    
    with pytest.raises(InferenceError): await cb.call(mock_fail)
    with pytest.raises(InferenceError): await cb.call(mock_fail)
    
    assert cb.state == CircuitState.OPEN
    with pytest.raises(CircuitOpenError):
        await cb.call(mock_fail)

@pytest.mark.asyncio
async def test_circuit_allows_one_call_in_half_open():
    cb = CircuitBreaker(CircuitBreakerConfig("test", failure_threshold=1, timeout_seconds=0.1))
    mock_fail = AsyncMock(side_effect=InferenceError())
    mock_success = AsyncMock(return_value="success")
    
    with pytest.raises(InferenceError): await cb.call(mock_fail) # Opens circuit
    assert cb.state == CircuitState.OPEN
    
    await asyncio.sleep(0.15) # Wait for timeout
    assert cb.state == CircuitState.HALF_OPEN
    
    result = await cb.call(mock_success)
    assert result == "success"

@pytest.mark.asyncio
async def test_circuit_reopens_on_half_open_failure():
    cb = CircuitBreaker(CircuitBreakerConfig("test", failure_threshold=1, timeout_seconds=0.1))
    mock_fail = AsyncMock(side_effect=InferenceError())
    
    with pytest.raises(InferenceError): await cb.call(mock_fail)
    await asyncio.sleep(0.15)
    
    assert cb.state == CircuitState.HALF_OPEN
    with pytest.raises(InferenceError): await cb.call(mock_fail)
    assert cb.state == CircuitState.OPEN
