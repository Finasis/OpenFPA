# OpenFP&A Frontend - Next.js Application

## Overview

A modern, responsive frontend application built with Next.js 14, TypeScript, and Tailwind CSS for the OpenFP&A Financial Planning & Analysis system.

## 🚀 Access Points

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

## 📁 Project Structure

```
frontend/
├── src/
│   ├── app/                    # Next.js App Router pages
│   │   ├── layout.tsx          # Root layout
│   │   ├── page.tsx            # Homepage/Dashboard
│   │   ├── companies/          # Companies CRUD pages
│   │   │   ├── page.tsx        # List companies
│   │   │   ├── new/            # Create company
│   │   │   └── [id]/           # View/Edit company
│   │   ├── cost-centers/       # Cost centers (placeholder)
│   │   ├── gl-accounts/        # GL accounts (placeholder)
│   │   ├── fiscal-periods/     # Fiscal periods (placeholder)
│   │   ├── scenarios/          # Budgets/Scenarios (placeholder)
│   │   └── transactions/       # Transactions (placeholder)
│   ├── components/             # Reusable components
│   │   ├── Navigation.tsx      # Main navigation
│   │   └── LoadingSpinner.tsx  # Loading indicator
│   ├── lib/                    # Utilities and API
│   │   └── api.ts             # API client with axios
│   └── types/                  # TypeScript type definitions
│       └── index.ts           # Shared types
├── public/                     # Static assets
├── package.json               # Dependencies
├── tsconfig.json              # TypeScript config
├── tailwind.config.js         # Tailwind CSS config
├── next.config.js             # Next.js config
└── Dockerfile                 # Production Docker config
```

## 🎯 Features Implemented

### Companies Module (Full CRUD)
- ✅ **List View**: Display all companies with status badges
- ✅ **Detail View**: Show complete company information
- ✅ **Create Form**: Add new companies with validation
- ✅ **Edit Form**: Update existing companies
- ✅ **Delete**: Remove companies with confirmation

### Navigation & Layout
- ✅ Responsive navigation bar
- ✅ Active route highlighting
- ✅ Clean, modern UI with Tailwind CSS

### API Integration
- ✅ Axios-based API client
- ✅ React Query for data fetching and caching
- ✅ Error handling with toast notifications
- ✅ Type-safe API calls with TypeScript

### Forms & Validation
- ✅ React Hook Form for form management
- ✅ Client-side validation
- ✅ Loading states and error handling

## 🛠️ Technology Stack

- **Framework**: Next.js 14 (App Router)
- **Language**: TypeScript
- **Styling**: Tailwind CSS
- **Data Fetching**: React Query (TanStack Query)
- **Forms**: React Hook Form
- **HTTP Client**: Axios
- **Notifications**: React Hot Toast
- **Date Handling**: date-fns

## 🐳 Docker Setup

### Development
```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f frontend

# Restart frontend
docker-compose restart frontend
```

### Production Build
```bash
# Build production image
docker build -t openfpa-frontend ./frontend

# Run production container
docker run -p 3000:3000 openfpa-frontend
```

## 🔧 Local Development

If you want to run the frontend locally (outside Docker):

```bash
cd frontend
npm install
npm run dev
```

## 📝 Environment Variables

Configure in `frontend/.env.local`:
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## 🎨 UI Components

### Dashboard Cards
Interactive cards for each module with icons and descriptions.

### Data Tables
Clean list views with:
- Status badges (Active/Inactive)
- Hover effects
- Click-to-view details

### Forms
Consistent form styling with:
- Labeled inputs
- Validation messages
- Submit/Cancel buttons
- Loading states

## 📚 API Integration Examples

### Fetching Data
```typescript
const { data, isLoading, error } = useQuery({
  queryKey: ['companies'],
  queryFn: async () => {
    const response = await companyApi.getAll();
    return response.data;
  },
});
```

### Creating Records
```typescript
const onSubmit = async (data: CompanyForm) => {
  try {
    await companyApi.create(data);
    toast.success('Company created successfully');
    router.push('/companies');
  } catch (error) {
    toast.error('Failed to create company');
  }
};
```

## 🚧 Placeholder Pages

The following modules have placeholder pages ready for implementation:
- Cost Centers
- GL Accounts
- Fiscal Periods
- Scenarios (Budgets)
- Transactions

## 🔄 Next Steps

To complete the remaining modules:

1. **Copy the Companies pattern** for other entities
2. **Update the API client** in `src/lib/api.ts`
3. **Add TypeScript types** in `src/types/index.ts`
4. **Create page components** following the same structure

## 🧪 Testing

To add tests:
```bash
npm install --save-dev @testing-library/react @testing-library/jest-dom jest jest-environment-jsdom
```

## 📦 Build & Deploy

### Production Build
```bash
npm run build
npm start
```

### Docker Production
```bash
docker build -t openfpa-frontend .
docker run -p 3000:3000 openfpa-frontend
```

## 🔗 Related Documentation

- [Next.js Documentation](https://nextjs.org/docs)
- [React Query Documentation](https://tanstack.com/query)
- [Tailwind CSS Documentation](https://tailwindcss.com/docs)
- [React Hook Form Documentation](https://react-hook-form.com)

## 🎯 Features Roadmap

- [ ] Authentication & Authorization
- [ ] Advanced filtering and search
- [ ] Export to CSV/Excel
- [ ] Charts and visualizations
- [ ] Bulk operations
- [ ] Audit trail viewing
- [ ] Real-time updates with WebSockets
- [ ] Dark mode support