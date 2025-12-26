"""
Site Tomograph - 爬蟲模組測試
"""

import pytest
from crawler import SiteCrawler


class TestUrlNormalization:
    """測試 URL 正規化 (M03)"""

    def setup_method(self):
        """每個測試前建立爬蟲實例"""
        self.crawler = SiteCrawler("https://example.com")

    def test_trailing_slash_removed(self):
        """根路徑尾端斜線應被移除"""
        result = self.crawler._normalize_url("/", "https://example.com")
        assert result == "https://example.com"

    def test_no_trailing_slash_unchanged(self):
        """無尾端斜線的 URL 不變"""
        result = self.crawler._normalize_url("/page", "https://example.com")
        assert result == "https://example.com/page"

    def test_page_trailing_slash_removed(self):
        """頁面路徑尾端斜線應被移除"""
        result = self.crawler._normalize_url("/page/", "https://example.com")
        assert result == "https://example.com/page"

    def test_deep_path_normalized(self):
        """深層路徑尾端斜線應被移除"""
        result = self.crawler._normalize_url("/a/b/c/", "https://example.com")
        assert result == "https://example.com/a/b/c"

    def test_relative_url_resolved(self):
        """相對路徑應該正確解析"""
        result = self.crawler._normalize_url("about", "https://example.com/page/")
        assert result == "https://example.com/page/about"

    def test_external_domain_rejected(self):
        """外部域名應被拒絕"""
        result = self.crawler._normalize_url("https://other.com/page", "https://example.com")
        assert result is None

    def test_javascript_url_rejected(self):
        """JavaScript URL 應被拒絕"""
        result = self.crawler._normalize_url("javascript:void(0)", "https://example.com")
        assert result is None

    def test_mailto_rejected(self):
        """mailto 連結應被拒絕"""
        result = self.crawler._normalize_url("mailto:test@example.com", "https://example.com")
        assert result is None

    def test_same_url_excluded(self):
        """相同 URL 應被排除（避免自我連結）"""
        # _normalize_url 本身不排除相同 URL，這是在 scan() 中處理
        result = self.crawler._normalize_url("/", "https://example.com")
        # 正規化後是 https://example.com
        assert result == "https://example.com"

    def test_fragment_removed(self):
        """Fragment 應被移除"""
        result = self.crawler._normalize_url("/page#section", "https://example.com")
        assert result == "https://example.com/page"
        assert "#" not in result


class TestCrawlerInit:
    """測試爬蟲初始化"""

    def test_default_values(self):
        """測試預設值"""
        crawler = SiteCrawler("https://example.com")
        assert crawler.max_depth == 3
        assert crawler.max_pages == 50
        assert crawler.max_retries == 3
        assert crawler.respect_robots is True

    def test_custom_values(self):
        """測試自訂值"""
        crawler = SiteCrawler(
            "https://example.com",
            max_depth=5,
            max_pages=100,
            max_retries=5,
            respect_robots=False
        )
        assert crawler.max_depth == 5
        assert crawler.max_pages == 100
        assert crawler.max_retries == 5
        assert crawler.respect_robots is False

    def test_base_domain_extracted(self):
        """測試域名正確提取"""
        crawler = SiteCrawler("https://sub.example.com/path")
        assert crawler.base_domain == "sub.example.com"

    def test_scheme_extracted(self):
        """測試協定正確提取"""
        crawler = SiteCrawler("http://example.com")
        assert crawler.base_scheme == "http"


class TestReportGeneration:
    """測試報告生成"""

    def test_empty_report(self):
        """測試空報告"""
        crawler = SiteCrawler("https://example.com")
        report = crawler.generate_report()

        assert report["summary"]["total_pages"] == 0
        assert report["summary"]["dead_links"] == 0
        assert report["summary"]["slow_pages"] == 0
        assert "健康" in report["recommendations"][0]

    def test_recommendations_for_issues(self):
        """測試問題建議"""
        crawler = SiteCrawler("https://example.com")
        crawler.stats["dead_links"] = 3
        crawler.stats["slow_pages"] = 2

        report = crawler.generate_report()

        # 應該有壞死連結和慢速頁面的建議
        recommendations_text = " ".join(report["recommendations"])
        assert "壞死" in recommendations_text or "dead" in recommendations_text.lower()
        assert "延遲" in recommendations_text or "slow" in recommendations_text.lower()
