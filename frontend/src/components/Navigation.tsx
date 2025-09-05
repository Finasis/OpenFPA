'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useState } from 'react';
import OpenFPALogo from './OpenFPALogo';

const navItems = [
  { href: '/companies', label: 'Companies', shortLabel: 'Companies', icon: '🏢' },
  { href: '/cost-centers', label: 'Cost Centers', shortLabel: 'Cost Centers', icon: '💻' },
  { href: '/gl-accounts', label: 'GL Accounts', shortLabel: 'GL Accounts', icon: '📋' },
  { href: '/fiscal-periods', label: 'Fiscal Periods', shortLabel: 'Periods', icon: '📅' },
  { href: '/scenarios', label: 'Budgets & Scenarios', shortLabel: 'Budgets', icon: '💰' },
  { href: '/transactions', label: 'Transactions', shortLabel: 'Transactions', icon: '💳' },
  { href: '/analytics', label: 'Analytics', shortLabel: 'Analytics', icon: '📈' },
  { href: '/planning', label: 'Planning', shortLabel: 'Planning', icon: '🎯' },
  { href: '/setup', label: 'Setup', shortLabel: 'Setup', icon: '⚙️' },
];

export function Navigation() {
  const pathname = usePathname();
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

  return (
    <nav className="bg-white shadow-md border-b border-gray-200">
      <div className="container mx-auto px-4">
        <div className="flex items-center justify-between h-16">
          <div className="flex items-center">
            <Link href="/" className="flex items-center mr-4 md:mr-6" title="Dashboard">
              <OpenFPALogo size="sm" />
            </Link>
            <div className="hidden md:flex items-center space-x-0.5">
              {/* First group: Core modules */}
              <div className="flex items-center space-x-0.5 pr-2 border-r border-gray-300">
                {navItems.slice(0, 6).map((item) => {
                  const isActive = pathname === item.href || pathname.startsWith(item.href);
                  
                  return (
                    <Link
                      key={item.href}
                      href={item.href}
                      title={item.label}
                      className={`group relative flex items-center px-3 py-2 rounded-md text-xs font-medium transition-all duration-200 ${
                        isActive
                          ? 'bg-gradient-to-r from-blue-500 to-blue-600 text-white shadow-sm'
                          : 'text-gray-600 hover:text-blue-600 hover:bg-blue-50'
                      }`}
                    >
                      <span className="mr-1.5 text-sm opacity-80 group-hover:opacity-100 transition-opacity">
                        {item.icon}
                      </span>
                      <span className="hidden lg:inline">{item.shortLabel}</span>
                      {isActive && (
                        <div className="absolute -bottom-0.5 left-1/2 transform -translate-x-1/2 w-1 h-1 bg-blue-300 rounded-full"></div>
                      )}
                    </Link>
                  );
                })}
              </div>

              {/* Second group: Analytics & Planning */}
              <div className="flex items-center space-x-0.5 px-2 border-r border-gray-300">
                {navItems.slice(6, 8).map((item) => {
                  const isActive = pathname === item.href || pathname.startsWith(item.href);
                  
                  return (
                    <Link
                      key={item.href}
                      href={item.href}
                      title={item.label}
                      className={`group relative flex items-center px-3 py-2 rounded-md text-xs font-medium transition-all duration-200 ${
                        isActive
                          ? 'bg-gradient-to-r from-blue-500 to-blue-600 text-white shadow-sm'
                          : 'text-gray-600 hover:text-blue-600 hover:bg-blue-50'
                      }`}
                    >
                      <span className="mr-1.5 text-sm opacity-80 group-hover:opacity-100 transition-opacity">
                        {item.icon}
                      </span>
                      <span className="hidden lg:inline">{item.shortLabel}</span>
                      {isActive && (
                        <div className="absolute -bottom-0.5 left-1/2 transform -translate-x-1/2 w-1 h-1 bg-blue-300 rounded-full"></div>
                      )}
                    </Link>
                  );
                })}
              </div>

              {/* Third group: Setup */}
              <div className="flex items-center space-x-0.5 pl-2">
                {navItems.slice(8).map((item) => {
                  const isActive = pathname === item.href || pathname.startsWith(item.href);
                  
                  return (
                    <Link
                      key={item.href}
                      href={item.href}
                      title={item.label}
                      className={`group relative flex items-center px-3 py-2 rounded-md text-xs font-medium transition-all duration-200 ${
                        isActive
                          ? 'bg-gradient-to-r from-blue-500 to-blue-600 text-white shadow-sm'
                          : 'text-gray-600 hover:text-blue-600 hover:bg-blue-50'
                      }`}
                    >
                      <span className="mr-1.5 text-sm opacity-80 group-hover:opacity-100 transition-opacity">
                        {item.icon}
                      </span>
                      <span className="hidden lg:inline">{item.shortLabel}</span>
                      {isActive && (
                        <div className="absolute -bottom-0.5 left-1/2 transform -translate-x-1/2 w-1 h-1 bg-blue-300 rounded-full"></div>
                      )}
                    </Link>
                  );
                })}
              </div>
            </div>
            
          </div>
          
          {/* Mobile menu button */}
          <div className="md:hidden">
            <button 
              onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
              className="flex items-center justify-center w-10 h-10 rounded-md text-gray-600 hover:text-gray-900 hover:bg-gray-100"
            >
              {isMobileMenuOpen ? (
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              ) : (
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
                </svg>
              )}
            </button>
          </div>
        </div>
        
        {/* Mobile menu dropdown */}
        {isMobileMenuOpen && (
          <div className="md:hidden border-t border-gray-200">
            <div className="px-2 pt-2 pb-3 space-y-1">
              {navItems.map((item) => {
                const isActive = pathname === item.href || pathname.startsWith(item.href);
                
                return (
                  <Link
                    key={item.href}
                    href={item.href}
                    onClick={() => setIsMobileMenuOpen(false)}
                    className={`block px-3 py-2 rounded-md text-base font-medium transition-all duration-200 ${
                      isActive
                        ? 'bg-blue-50 text-blue-700 border-l-4 border-blue-500'
                        : 'text-gray-700 hover:text-gray-900 hover:bg-gray-50'
                    }`}
                  >
                    <span className="mr-3 text-lg">{item.icon}</span>
                    {item.label}
                  </Link>
                );
              })}
            </div>
          </div>
        )}
      </div>
    </nav>
  );
}