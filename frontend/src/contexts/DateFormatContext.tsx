'use client';

import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';

export type DateFormat = 'DD/MM/YYYY' | 'MM/DD/YYYY' | 'YYYY-MM-DD';

interface DateFormatContextType {
  dateFormat: DateFormat;
  setDateFormat: (format: DateFormat) => void;
  formatDate: (dateString: string | Date) => string;
}

const DateFormatContext = createContext<DateFormatContextType | undefined>(undefined);

export function DateFormatProvider({ children }: { children: ReactNode }) {
  const [dateFormat, setDateFormatState] = useState<DateFormat>('DD/MM/YYYY');

  // Load saved format from localStorage on mount
  useEffect(() => {
    const savedFormat = localStorage.getItem('dateFormat') as DateFormat;
    if (savedFormat && ['DD/MM/YYYY', 'MM/DD/YYYY', 'YYYY-MM-DD'].includes(savedFormat)) {
      setDateFormatState(savedFormat);
    }
  }, []);

  const setDateFormat = (format: DateFormat) => {
    setDateFormatState(format);
    localStorage.setItem('dateFormat', format);
  };

  const formatDate = (dateString: string | Date): string => {
    try {
      const date = typeof dateString === 'string' ? new Date(dateString) : dateString;
      
      if (isNaN(date.getTime())) {
        return 'Invalid Date';
      }

      const day = String(date.getDate()).padStart(2, '0');
      const month = String(date.getMonth() + 1).padStart(2, '0');
      const year = date.getFullYear();

      switch (dateFormat) {
        case 'DD/MM/YYYY':
          return `${day}/${month}/${year}`;
        case 'MM/DD/YYYY':
          return `${month}/${day}/${year}`;
        case 'YYYY-MM-DD':
          return `${year}-${month}-${day}`;
        default:
          return `${day}/${month}/${year}`;
      }
    } catch (error) {
      console.error('Date formatting error:', error);
      return 'Invalid Date';
    }
  };

  return (
    <DateFormatContext.Provider value={{ dateFormat, setDateFormat, formatDate }}>
      {children}
    </DateFormatContext.Provider>
  );
}

export function useDateFormat() {
  const context = useContext(DateFormatContext);
  if (context === undefined) {
    throw new Error('useDateFormat must be used within a DateFormatProvider');
  }
  return context;
}

// Standalone formatting function for when context isn't available
export function formatDateStandalone(dateString: string | Date, format: DateFormat = 'DD/MM/YYYY'): string {
  try {
    const date = typeof dateString === 'string' ? new Date(dateString) : dateString;
    
    if (isNaN(date.getTime())) {
      return 'Invalid Date';
    }

    const day = String(date.getDate()).padStart(2, '0');
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const year = date.getFullYear();

    switch (format) {
      case 'DD/MM/YYYY':
        return `${day}/${month}/${year}`;
      case 'MM/DD/YYYY':
        return `${month}/${day}/${year}`;
      case 'YYYY-MM-DD':
        return `${year}-${month}-${day}`;
      default:
        return `${day}/${month}/${year}`;
    }
  } catch (error) {
    console.error('Date formatting error:', error);
    return 'Invalid Date';
  }
}