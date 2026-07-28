import React from 'react';
import { BrandProvider } from './brands/BrandProvider';
import { GosaDashboard } from './pages/GosaDashboard';

export default function App() {
  return (
    <BrandProvider defaultBrandId="columbia-county">
      <GosaDashboard />
    </BrandProvider>
  );
}
