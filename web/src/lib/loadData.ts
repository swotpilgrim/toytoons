import { readFileSync } from 'fs';
import { join } from 'path';

export interface Listing {
  show_title?: string;
  toyline_name?: string;
  slug?: string;
  era?: string;
  years_aired?: string;
  years_toyline?: string;
  manufacturer?: string;
  country?: string;
  studio_network?: string;
  description_summary?: string;
  notable_characters: string[];
  main_image_url?: string;
  main_image_local?: string;
  additional_images?: Array<{
    url: string;
    local: string;
    description: string;
  }>;
  source_url: string;
  source_title?: string;
  first_seen: string;
  parse_notes: string[];
  category?: string;
}

export function loadListings(): Listing[] {
  try {
    const dataPath = join(process.cwd(), 'src', 'data', 'listings.json');
    const jsonData = readFileSync(dataPath, 'utf-8');
    return JSON.parse(jsonData);
  } catch (error) {
    console.warn('Could not load listings data:', error);
    
    // Return sample data for development
    return [
      {
        show_title: "Transformers",
        toyline_name: "Transformers",
        slug: "transformers",
        era: "1980s",
        years_aired: "1984-1987",
        years_toyline: "1984-1990",
        manufacturer: "Hasbro",
        country: "United States",
        studio_network: "Sunbow Productions",
        description_summary: "Robots in disguise that transform from vehicles to humanoid robots, engaged in an eternal battle between Autobots and Decepticons. The toy line became one of the most successful action figure franchises of the 1980s.",
        notable_characters: ["Optimus Prime", "Megatron", "Bumblebee", "Starscream"],
        main_image_url: "",
        main_image_local: "",
        additional_images: [],
        source_url: "https://example.com/transformers",
        source_title: "Transformers - More Than Meets The Eye",
        first_seen: "2024-01-01T00:00:00Z",
        parse_notes: ["Sample data for development"]
      },
      {
        show_title: "G.I. Joe",
        toyline_name: "G.I. Joe: A Real American Hero",
        slug: "gi-joe-real-american-hero",
        era: "1980s",
        years_aired: "1985-1986",
        years_toyline: "1982-1994",
        manufacturer: "Hasbro",
        country: "United States",
        studio_network: "Sunbow Productions",
        description_summary: "Military-themed action figures and cartoon featuring the heroic G.I. Joe team fighting against the terrorist organization Cobra. Known for its detailed 3.75-inch figures and vehicles.",
        notable_characters: ["Duke", "Snake Eyes", "Cobra Commander", "Destro"],
        main_image_url: "",
        main_image_local: "",
        additional_images: [],
        source_url: "https://example.com/gi-joe",
        source_title: "G.I. Joe: A Real American Hero",
        first_seen: "2024-01-01T00:00:00Z",
        parse_notes: ["Sample data for development"]
      },
      {
        show_title: "He-Man and the Masters of the Universe",
        toyline_name: "Masters of the Universe",
        slug: "he-man-masters-of-the-universe",
        era: "1980s",
        years_aired: "1983-1985",
        years_toyline: "1982-1987",
        manufacturer: "Mattel",
        country: "United States",
        studio_network: "Filmation",
        description_summary: "Prince Adam transforms into the mighty He-Man to defend Castle Grayskull and planet Eternia from the evil Skeletor. The toy line featured distinctive muscular action figures and fantastical creatures.",
        notable_characters: ["He-Man", "Skeletor", "Battle Cat", "Man-At-Arms"],
        main_image_url: "",
        main_image_local: "",
        additional_images: [],
        source_url: "https://example.com/he-man",
        source_title: "He-Man and the Masters of the Universe",
        first_seen: "2024-01-01T00:00:00Z",
        parse_notes: ["Sample data for development"]
      }
    ];
  }
}

export function getListingBySlug(slug: string): Listing | undefined {
  const listings = loadListings();
  return listings.find(listing => listing.slug === slug);
}

export function getUniqueEras(listings: Listing[]): string[] {
  const eras = new Set(listings.map(l => l.era).filter(Boolean));
  return Array.from(eras).sort();
}

export function getUniqueManufacturers(listings: Listing[]): string[] {
  const manufacturers = new Set(listings.map(l => l.manufacturer).filter(Boolean));
  return Array.from(manufacturers).sort();
}

export function getUniqueCategories(listings: Listing[]): string[] {
  const categories = new Set(listings.map(l => l.category).filter(Boolean));
  return Array.from(categories).sort();
}