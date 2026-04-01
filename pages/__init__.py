"""
Page Object Model (POM) Package

This package contains Playwright page objects for UI testing.
Each page object encapsulates the locators and interactions
for a specific page in the application.

Usage:
    from pages import LoginPage, DashboardPage, DevicesPage, AlertsPage
    
    login_page = LoginPage(page, base_url)
    login_page.login("admin", "password")
"""

from pages.alerts_page import AlertsPage
from pages.base_page import BasePage
from pages.dashboard_page import DashboardPage
from pages.devices_page import DevicesPage
from pages.login_page import LoginPage

__all__ = [
    "BasePage",
    "LoginPage",
    "DashboardPage",
    "DevicesPage",
    "AlertsPage",
]
