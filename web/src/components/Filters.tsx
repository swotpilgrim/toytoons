import React, { useState, useEffect } from 'react';
import type { Listing } from '../lib/loadData';

interface Props {
  listings: Listing[];
  onFilter: (filtered: Listing[]) => void;
  eras: string[];
  manufacturers: string[];
}

export default function Filters({ listings, onFilter, eras, manufacturers }: Props) {
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedEras, setSelectedEras] = useState<Set<string>>(new Set());
  const [selectedManufacturers, setSelectedManufacturers] = useState<Set<string>>(new Set());
  const [isFiltersOpen, setIsFiltersOpen] = useState(false);

  // Apply filters whenever inputs change
  useEffect(() => {
    let filtered = listings;

    // Text search
    if (searchTerm.trim()) {
      const searchLower = searchTerm.toLowerCase();
      filtered = filtered.filter(listing => 
        (listing.show_title?.toLowerCase().includes(searchLower)) ||
        (listing.toyline_name?.toLowerCase().includes(searchLower)) ||
        (listing.manufacturer?.toLowerCase().includes(searchLower)) ||
        (listing.notable_characters?.some(char => char.toLowerCase().includes(searchLower)))
      );
    }

    // Era filter
    if (selectedEras.size > 0) {
      filtered = filtered.filter(listing => 
        listing.era && selectedEras.has(listing.era)
      );
    }

    // Manufacturer filter
    if (selectedManufacturers.size > 0) {
      filtered = filtered.filter(listing => 
        listing.manufacturer && selectedManufacturers.has(listing.manufacturer)
      );
    }

    onFilter(filtered);
  }, [searchTerm, selectedEras, selectedManufacturers, listings, onFilter]);

  const toggleEra = (era: string) => {
    const newSet = new Set(selectedEras);
    if (newSet.has(era)) {
      newSet.delete(era);
    } else {
      newSet.add(era);
    }
    setSelectedEras(newSet);
  };

  const toggleManufacturer = (manufacturer: string) => {
    const newSet = new Set(selectedManufacturers);
    if (newSet.has(manufacturer)) {
      newSet.delete(manufacturer);
    } else {
      newSet.add(manufacturer);
    }
    setSelectedManufacturers(newSet);
  };

  const clearAllFilters = () => {
    setSearchTerm('');
    setSelectedEras(new Set());
    setSelectedManufacturers(new Set());
  };

  const activeFiltersCount = selectedEras.size + selectedManufacturers.size + (searchTerm ? 1 : 0);

  return (
    <div className="bg-white rounded-lg shadow-md p-6 mb-8">
      {/* Search Bar */}
      <div className="mb-6">
        <label htmlFor="search" className="block text-sm font-medium text-gray-700 mb-2">
          Search shows, toys, characters...
        </label>
        <div className="relative">
          <input
            type="text"
            id="search"
            className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
            placeholder="Try 'Transformers', 'Hasbro', or 'Optimus Prime'..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
          <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
            <svg className="h-5 w-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
          </div>
        </div>
      </div>

      {/* Filters Toggle */}
      <div className="flex items-center justify-between mb-4">
        <button
          onClick={() => setIsFiltersOpen(!isFiltersOpen)}
          className="flex items-center space-x-2 text-gray-700 hover:text-primary-600 transition-colors"
        >
          <svg 
            className={`w-5 h-5 transition-transform ${isFiltersOpen ? 'rotate-90' : ''}`}
            fill="none" 
            stroke="currentColor" 
            viewBox="0 0 24 24"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 5l7 7-7 7" />
          </svg>
          <span className="font-medium">Filters</span>
          {activeFiltersCount > 0 && (
            <span className="bg-primary-100 text-primary-800 px-2 py-1 rounded-full text-sm">
              {activeFiltersCount}
            </span>
          )}
        </button>

        {activeFiltersCount > 0 && (
          <button
            onClick={clearAllFilters}
            className="text-sm text-gray-500 hover:text-gray-700 underline"
          >
            Clear all
          </button>
        )}
      </div>

      {/* Filter Options */}
      {isFiltersOpen && (
        <div className="grid md:grid-cols-2 gap-6 pt-4 border-t border-gray-200">
          {/* Era Filter */}
          <div>
            <h3 className="font-medium text-gray-900 mb-3">Era</h3>
            <div className="space-y-2">
              {eras.map(era => (
                <label key={era} className="flex items-center cursor-pointer">
                  <input
                    type="checkbox"
                    className="rounded border-gray-300 text-primary-600 focus:ring-primary-500"
                    checked={selectedEras.has(era)}
                    onChange={() => toggleEra(era)}
                  />
                  <span className="ml-2 text-sm text-gray-700">{era}</span>
                </label>
              ))}
            </div>
          </div>

          {/* Manufacturer Filter */}
          <div>
            <h3 className="font-medium text-gray-900 mb-3">Manufacturer</h3>
            <div className="space-y-2">
              {manufacturers.map(manufacturer => (
                <label key={manufacturer} className="flex items-center cursor-pointer">
                  <input
                    type="checkbox"
                    className="rounded border-gray-300 text-primary-600 focus:ring-primary-500"
                    checked={selectedManufacturers.has(manufacturer)}
                    onChange={() => toggleManufacturer(manufacturer)}
                  />
                  <span className="ml-2 text-sm text-gray-700">{manufacturer}</span>
                </label>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}