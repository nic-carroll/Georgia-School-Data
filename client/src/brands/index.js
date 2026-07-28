import './columbia-county/theme.css';
import './georgia-southern/theme.css';

import { columbiaCountyBrand } from './columbia-county/brandConfig';
import { georgiaSouthernBrand } from './georgia-southern/brandConfig';

export const defaultBrand = {
  id: 'default',
  name: 'Standard Application',
  shortName: 'App',
  location: 'Global',
  tagline: 'Interactive Application',
  website: '#',
  logoUrl: '/brands/default/logo.svg',
  colors: {
    primary: '#1E293B',
    secondary: '#6366F1',
    accent: '#3B82F6',
    background: '#F8FAFC',
    text: '#0F172A'
  }
};

export const BRANDS = {
  'columbia-county': columbiaCountyBrand,
  'georgia-southern': georgiaSouthernBrand,
  'default': defaultBrand
};

export function getBrandConfig(brandId) {
  return BRANDS[brandId] || BRANDS['default'];
}
