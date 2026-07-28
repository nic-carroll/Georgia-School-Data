import React, { createContext, useContext, useState, useEffect } from 'react';
import { BRANDS, getBrandConfig } from './index';

const BrandContext = createContext({
  activeBrand: BRANDS['columbia-county'],
  brandId: 'columbia-county',
  setBrand: () => {},
  availableBrands: BRANDS
});

export function BrandProvider({ children, defaultBrandId = 'columbia-county' }) {
  const [brandId, setBrandId] = useState(defaultBrandId);
  const activeBrand = getBrandConfig(brandId);

  useEffect(() => {
    // Inject attribute on document.documentElement to scope CSS variables
    document.documentElement.setAttribute('data-brand', brandId);
  }, [brandId]);

  return (
    <BrandContext.Provider value={{ activeBrand, brandId, setBrand: setBrandId, availableBrands: BRANDS }}>
      {children}
    </BrandContext.Provider>
  );
}

export function useBrand() {
  return useContext(BrandContext);
}
