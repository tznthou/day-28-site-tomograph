"""
Site Tomograph - 安全模組測試
"""

import pytest
from security import (
    is_private_ip,
    validate_url_safety,
    sanitize_url_for_display,
    sanitize_error_message,
    ScanRequest,
    RateLimiter,
)


class TestIsPrivateIP:
    """測試私有 IP 檢測"""

    def test_loopback_ipv4(self):
        assert is_private_ip("127.0.0.1") is True

    def test_loopback_ipv6(self):
        assert is_private_ip("::1") is True

    def test_private_class_a(self):
        assert is_private_ip("10.0.0.1") is True
        assert is_private_ip("10.255.255.255") is True

    def test_private_class_b(self):
        assert is_private_ip("172.16.0.1") is True
        assert is_private_ip("172.31.255.255") is True

    def test_private_class_c(self):
        assert is_private_ip("192.168.0.1") is True
        assert is_private_ip("192.168.255.255") is True

    def test_public_ip(self):
        assert is_private_ip("8.8.8.8") is False
        assert is_private_ip("1.1.1.1") is False

    def test_invalid_ip(self):
        assert is_private_ip("not-an-ip") is False
        assert is_private_ip("") is False


class TestValidateUrlSafety:
    """測試 URL 安全驗證"""

    def test_valid_https_url(self):
        is_safe, error = validate_url_safety("https://example.com")
        assert is_safe is True
        assert error == ""

    def test_valid_http_url(self):
        is_safe, error = validate_url_safety("http://example.com")
        assert is_safe is True
        assert error == ""

    def test_localhost_blocked(self):
        is_safe, error = validate_url_safety("http://localhost")
        assert is_safe is False
        assert "不允許" in error

    def test_loopback_blocked(self):
        is_safe, error = validate_url_safety("http://127.0.0.1")
        assert is_safe is False

    def test_metadata_endpoint_blocked(self):
        is_safe, error = validate_url_safety("http://169.254.169.254")
        assert is_safe is False

    def test_private_ip_blocked(self):
        is_safe, error = validate_url_safety("http://192.168.1.1")
        assert is_safe is False
        assert "私有" in error

    def test_invalid_protocol(self):
        is_safe, error = validate_url_safety("ftp://example.com")
        assert is_safe is False
        assert "HTTP" in error

    def test_dangerous_port_blocked(self):
        is_safe, error = validate_url_safety("https://example.com:22")
        assert is_safe is False
        assert "port" in error

    def test_missing_hostname(self):
        is_safe, error = validate_url_safety("https://")
        assert is_safe is False


class TestSanitizeUrlForDisplay:
    """測試 URL 清理"""

    def test_removes_userinfo(self):
        result = sanitize_url_for_display("https://user:pass@example.com/path")
        assert "user" not in result
        assert "pass" not in result
        assert "example.com" in result

    def test_preserves_path(self):
        result = sanitize_url_for_display("https://example.com/some/path")
        assert "/some/path" in result

    def test_malformed_url(self):
        # urlparse 不會對格式錯誤的 URL 拋出異常，只會解析成路徑
        # 這個測試確認函式不會崩潰
        result = sanitize_url_for_display("not-a-valid-url")
        assert isinstance(result, str)


class TestSanitizeErrorMessage:
    """測試錯誤訊息清理"""

    def test_removes_file_paths(self):
        error = Exception("/home/user/secret/file.py crashed")
        result = sanitize_error_message(error)
        assert "/home/" not in result

    def test_masks_internal_ip(self):
        error = Exception("Connection to 192.168.1.100 failed")
        result = sanitize_error_message(error)
        assert "192.168." not in result
        assert "[內部IP]" in result

    def test_truncates_long_message(self):
        long_message = "x" * 500
        error = Exception(long_message)
        result = sanitize_error_message(error)
        assert len(result) <= 203  # 200 + "..."


class TestScanRequest:
    """測試掃描請求驗證"""

    def test_valid_url(self):
        req = ScanRequest(url="https://example.com")
        assert req.url == "https://example.com"

    def test_auto_adds_https(self):
        req = ScanRequest(url="example.com")
        assert req.url == "https://example.com"

    def test_strips_whitespace(self):
        req = ScanRequest(url="  https://example.com  ")
        assert req.url == "https://example.com"

    def test_empty_url_rejected(self):
        with pytest.raises(ValueError):
            ScanRequest(url="")

    def test_too_long_url_rejected(self):
        long_url = "https://example.com/" + "a" * 3000
        with pytest.raises(ValueError):
            ScanRequest(url=long_url)


class TestRateLimiter:
    """測試速率限制器"""

    @pytest.mark.asyncio
    async def test_allows_first_request(self):
        limiter = RateLimiter(requests_per_minute=5)
        allowed, error = await limiter.check_rate_limit("1.2.3.4")
        assert allowed is True
        assert error == ""
        await limiter.release_scan()

    @pytest.mark.asyncio
    async def test_blocks_after_limit(self):
        limiter = RateLimiter(requests_per_minute=2)

        # 第 1-2 次應該允許
        await limiter.check_rate_limit("1.2.3.4")
        await limiter.check_rate_limit("1.2.3.4")

        # 第 3 次應該被阻擋
        allowed, error = await limiter.check_rate_limit("1.2.3.4")
        assert allowed is False
        assert "頻繁" in error

    @pytest.mark.asyncio
    async def test_different_ips_independent(self):
        limiter = RateLimiter(requests_per_minute=1)

        allowed1, _ = await limiter.check_rate_limit("1.1.1.1")
        allowed2, _ = await limiter.check_rate_limit("2.2.2.2")

        assert allowed1 is True
        assert allowed2 is True

    @pytest.mark.asyncio
    async def test_concurrent_scan_limit(self):
        limiter = RateLimiter(max_concurrent_scans=2)

        await limiter.check_rate_limit("1.1.1.1")
        await limiter.check_rate_limit("2.2.2.2")

        # 第 3 個應該被阻擋
        allowed, error = await limiter.check_rate_limit("3.3.3.3")
        assert allowed is False
        assert "繁忙" in error

    @pytest.mark.asyncio
    async def test_release_scan(self):
        limiter = RateLimiter(max_concurrent_scans=1)

        await limiter.check_rate_limit("1.1.1.1")
        await limiter.release_scan()

        # 釋放後應該可以再次請求
        allowed, _ = await limiter.check_rate_limit("2.2.2.2")
        assert allowed is True
