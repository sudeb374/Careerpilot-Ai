/**
 * Location Service for CareerPilot AI
 *
 * Provides city and locality autocomplete with Indian postal code and district coverage.
 *
 * Data Sources (Free, Low-Cost, Documented, No API key required):
 * 1. Primary: Department of Posts, Government of India (via official Postal Pincode API: https://api.postalpincode.in/)
 * 2. Secondary / Administrative: OpenStreetMap Nominatim Geocoding API for India (https://nominatim.openstreetmap.org/)
 * 3. Curated Local Verified Index: Major Indian tech hubs, metropolitan localities, and IT corridors
 *
 * Coverage & Limitations:
 * - Covers all 28 states and 8 union territories of India with official Post Office names, districts, states, and PIN codes.
 * - Does not store sensitive full street addresses; only locality, city/district, state, and optional PIN needed for opportunity matching.
 * - Nominatim requests are debounced and use custom User-Agent headers compliant with OSM usage policy.
 * - Custom freeform location input is always supported as a seamless fallback if external APIs are unreachable or offline.
 */

export interface LocationSuggestion {
  name: string;
  district?: string;
  state: string;
  pincode?: string;
  displayName: string;
  value: string;
  isCustom?: boolean;
}

// Curated verified Indian tech hubs and metropolitan localities for instant, offline-resilient matching
const VERIFIED_TECH_HUBS: LocationSuggestion[] = [
  // Kolkata / West Bengal
  { name: "Sector V", district: "Kolkata", state: "West Bengal", pincode: "700091", displayName: "Sector V, Salt Lake, Kolkata, West Bengal (700091)", value: "Sector V, Kolkata, West Bengal" },
  { name: "Salt Lake", district: "Kolkata / North 24 Parganas", state: "West Bengal", pincode: "700091", displayName: "Salt Lake (Bidhannagar), Kolkata, West Bengal (700091)", value: "Salt Lake, Kolkata, West Bengal" },
  { name: "New Town", district: "Kolkata / North 24 Parganas", state: "West Bengal", pincode: "700156", displayName: "New Town, Kolkata, West Bengal (700156)", value: "New Town, Kolkata, West Bengal" },
  { name: "Rajarhat", district: "Kolkata / North 24 Parganas", state: "West Bengal", pincode: "700135", displayName: "Rajarhat, Kolkata, West Bengal (700135)", value: "Rajarhat, Kolkata, West Bengal" },
  { name: "Park Street", district: "Kolkata", state: "West Bengal", pincode: "700016", displayName: "Park Street, Kolkata, West Bengal (700016)", value: "Park Street, Kolkata, West Bengal" },
  { name: "Kolkata Central", district: "Kolkata", state: "West Bengal", pincode: "700001", displayName: "Kolkata, West Bengal (700001)", value: "Kolkata, West Bengal" },

  // Pune / Maharashtra
  { name: "Hinjawadi", district: "Pune", state: "Maharashtra", pincode: "411057", displayName: "Hinjawadi Infotech Park, Pune, Maharashtra (411057)", value: "Hinjawadi, Pune, Maharashtra" },
  { name: "Kharadi", district: "Pune", state: "Maharashtra", pincode: "411014", displayName: "Kharadi (EON Free Zone), Pune, Maharashtra (411014)", value: "Kharadi, Pune, Maharashtra" },
  { name: "Viman Nagar", district: "Pune", state: "Maharashtra", pincode: "411014", displayName: "Viman Nagar, Pune, Maharashtra (411014)", value: "Viman Nagar, Pune, Maharashtra" },
  { name: "Magarpatta City", district: "Pune", state: "Maharashtra", pincode: "411028", displayName: "Magarpatta Cybercity, Pune, Maharashtra (411028)", value: "Magarpatta, Pune, Maharashtra" },
  { name: "Baner", district: "Pune", state: "Maharashtra", pincode: "411045", displayName: "Baner, Pune, Maharashtra (411045)", value: "Baner, Pune, Maharashtra" },
  { name: "Shivajinagar", district: "Pune", state: "Maharashtra", pincode: "411005", displayName: "Shivajinagar, Pune, Maharashtra (411005)", value: "Shivajinagar, Pune, Maharashtra" },
  { name: "Pune", district: "Pune", state: "Maharashtra", pincode: "411001", displayName: "Pune, Maharashtra (411001)", value: "Pune, Maharashtra" },

  // Bengaluru / Karnataka
  { name: "Koramangala", district: "Bengaluru Urban", state: "Karnataka", pincode: "560034", displayName: "Koramangala, Bengaluru, Karnataka (560034)", value: "Koramangala, Bengaluru, Karnataka" },
  { name: "Whitefield", district: "Bengaluru Urban", state: "Karnataka", pincode: "560066", displayName: "Whitefield (ITPB), Bengaluru, Karnataka (560066)", value: "Whitefield, Bengaluru, Karnataka" },
  { name: "Electronic City", district: "Bengaluru Urban", state: "Karnataka", pincode: "560100", displayName: "Electronic City, Bengaluru, Karnataka (560100)", value: "Electronic City, Bengaluru, Karnataka" },
  { name: "Indiranagar", district: "Bengaluru Urban", state: "Karnataka", pincode: "560038", displayName: "Indiranagar, Bengaluru, Karnataka (560038)", value: "Indiranagar, Bengaluru, Karnataka" },
  { name: "HSR Layout", district: "Bengaluru Urban", state: "Karnataka", pincode: "560102", displayName: "HSR Layout, Bengaluru, Karnataka (560102)", value: "HSR Layout, Bengaluru, Karnataka" },
  { name: "Bellandur", district: "Bengaluru Urban", state: "Karnataka", pincode: "560103", displayName: "Bellandur Outer Ring Road, Bengaluru, Karnataka (560103)", value: "Bellandur, Bengaluru, Karnataka" },
  { name: "Bengaluru", district: "Bengaluru Urban", state: "Karnataka", pincode: "560001", displayName: "Bengaluru, Karnataka (560001)", value: "Bengaluru, Karnataka" },

  // Hyderabad / Telangana
  { name: "Hitec City", district: "Hyderabad", state: "Telangana", pincode: "500081", displayName: "HITEC City, Madhapur, Hyderabad, Telangana (500081)", value: "HITEC City, Hyderabad, Telangana" },
  { name: "Gachibowli", district: "Hyderabad", state: "Telangana", pincode: "500032", displayName: "Gachibowli Financial District, Hyderabad, Telangana (500032)", value: "Gachibowli, Hyderabad, Telangana" },
  { name: "Madhapur", district: "Hyderabad", state: "Telangana", pincode: "500081", displayName: "Madhapur, Hyderabad, Telangana (500081)", value: "Madhapur, Hyderabad, Telangana" },
  { name: "Hyderabad", district: "Hyderabad", state: "Telangana", pincode: "500001", displayName: "Hyderabad, Telangana (500001)", value: "Hyderabad, Telangana" },

  // Mumbai / Maharashtra
  { name: "Bandra Kurla Complex (BKC)", district: "Mumbai Suburban", state: "Maharashtra", pincode: "400051", displayName: "BKC (Bandra Kurla Complex), Mumbai, Maharashtra (400051)", value: "BKC, Mumbai, Maharashtra" },
  { name: "Powai", district: "Mumbai Suburban", state: "Maharashtra", pincode: "400076", displayName: "Powai, Mumbai, Maharashtra (400076)", value: "Powai, Mumbai, Maharashtra" },
  { name: "Andheri East", district: "Mumbai Suburban", state: "Maharashtra", pincode: "400069", displayName: "Andheri East (SEEPZ), Mumbai, Maharashtra (400069)", value: "Andheri East, Mumbai, Maharashtra" },
  { name: "Navi Mumbai", district: "Thane", state: "Maharashtra", pincode: "400703", displayName: "Navi Mumbai (Vashi / Airoli), Maharashtra (400703)", value: "Navi Mumbai, Maharashtra" },
  { name: "Mumbai", district: "Mumbai", state: "Maharashtra", pincode: "400001", displayName: "Mumbai, Maharashtra (400001)", value: "Mumbai, Maharashtra" },

  // Delhi NCR
  { name: "Cyber City", district: "Gurugram", state: "Haryana", pincode: "122002", displayName: "DLF Cyber City, Gurugram, Haryana (122002)", value: "Cyber City, Gurugram, Haryana" },
  { name: "Gurugram", district: "Gurugram", state: "Haryana", pincode: "122001", displayName: "Gurugram (Gurgaon), Haryana (122001)", value: "Gurugram, Haryana" },
  { name: "Sector 62 Noida", district: "Gautam Buddha Nagar", state: "Uttar Pradesh", pincode: "201309", displayName: "Sector 62, Noida, Uttar Pradesh (201309)", value: "Sector 62, Noida, Uttar Pradesh" },
  { name: "Noida", district: "Gautam Buddha Nagar", state: "Uttar Pradesh", pincode: "201301", displayName: "Noida, Uttar Pradesh (201301)", value: "Noida, Uttar Pradesh" },
  { name: "Connaught Place", district: "New Delhi", state: "Delhi", pincode: "110001", displayName: "Connaught Place, New Delhi, Delhi (110001)", value: "Connaught Place, New Delhi, Delhi" },
  { name: "New Delhi", district: "New Delhi", state: "Delhi", pincode: "110001", displayName: "New Delhi, Delhi (110001)", value: "New Delhi, Delhi" },

  // Chennai / Tamil Nadu
  { name: "OMR (Old Mahabalipuram Road)", district: "Chennai", state: "Tamil Nadu", pincode: "600096", displayName: "OMR IT Corridor, Chennai, Tamil Nadu (600096)", value: "OMR, Chennai, Tamil Nadu" },
  { name: "Guindy", district: "Chennai", state: "Tamil Nadu", pincode: "600032", displayName: "Guindy Industrial Estate, Chennai, Tamil Nadu (600032)", value: "Guindy, Chennai, Tamil Nadu" },
  { name: "T. Nagar", district: "Chennai", state: "Tamil Nadu", pincode: "600017", displayName: "T. Nagar, Chennai, Tamil Nadu (600017)", value: "T. Nagar, Chennai, Tamil Nadu" },
  { name: "Chennai", district: "Chennai", state: "Tamil Nadu", pincode: "600001", displayName: "Chennai, Tamil Nadu (600001)", value: "Chennai, Tamil Nadu" },
];

/**
 * Search localities and post offices from the official Postal Pincode API
 */
async function fetchFromPostalApi(query: string, signal?: AbortSignal): Promise<LocationSuggestion[]> {
  const isPincode = /^\d{3,6}$/.test(query.trim());
  const endpoint = isPincode
    ? `https://api.postalpincode.in/pincode/${encodeURIComponent(query.trim())}`
    : `https://api.postalpincode.in/postoffice/${encodeURIComponent(query.trim())}`;

  const res = await fetch(endpoint, { signal });
  if (!res.ok) {
    throw new Error(`Postal API responded with status ${res.status}`);
  }

  const data = await res.json();
  if (!Array.isArray(data) || !data[0] || data[0].Status !== "Success" || !Array.isArray(data[0].PostOffice)) {
    return [];
  }

  const suggestions: LocationSuggestion[] = [];
  const seen = new Set<string>();

  for (const po of data[0].PostOffice) {
    const name = po.Name || "";
    const district = po.District || "";
    const state = po.State || "";
    const pincode = po.Pincode || "";

    const key = `${name}-${district}-${state}-${pincode}`.toLowerCase();
    if (seen.has(key)) continue;
    seen.add(key);

    const displayName = `${name}${district && district !== name ? `, ${district}` : ""}, ${state}${pincode ? ` (${pincode})` : ""}`;
    const value = `${name}${district && district !== name ? `, ${district}` : ""}, ${state}`;

    suggestions.push({
      name,
      district,
      state,
      pincode,
      displayName,
      value,
    });

    if (suggestions.length >= 8) break;
  }

  return suggestions;
}

/**
 * Fallback to OpenStreetMap Nominatim for Indian administrative localities
 */
async function fetchFromNominatim(query: string, signal?: AbortSignal): Promise<LocationSuggestion[]> {
  const url = `https://nominatim.openstreetmap.org/search?q=${encodeURIComponent(query)}&countrycodes=in&format=json&addressdetails=1&limit=6`;
  const res = await fetch(url, {
    signal,
    headers: {
      "User-Agent": "CareerPilot-AI-Location-Autocomplete/1.0",
      "Accept-Language": "en",
    },
  });

  if (!res.ok) {
    throw new Error(`Nominatim responded with status ${res.status}`);
  }

  const items = await res.json();
  if (!Array.isArray(items)) return [];

  const suggestions: LocationSuggestion[] = [];
  const seen = new Set<string>();

  for (const item of items) {
    const addr = item.address || {};
    const name = addr.suburb || addr.neighbourhood || addr.city || addr.town || addr.village || item.name || "";
    const district = addr.state_district || addr.county || addr.city || "";
    const state = addr.state || "";
    const pincode = addr.postcode || "";

    if (!name || !state) continue;

    const key = `${name}-${district}-${state}`.toLowerCase();
    if (seen.has(key)) continue;
    seen.add(key);

    const displayName = `${name}${district && district !== name ? `, ${district}` : ""}, ${state}${pincode ? ` (${pincode})` : ""}`;
    const value = `${name}${district && district !== name ? `, ${district}` : ""}, ${state}`;

    suggestions.push({
      name,
      district,
      state,
      pincode,
      displayName,
      value,
    });
  }

  return suggestions;
}

/**
 * Search localities, cities, and postal codes across India
 */
export async function searchLocations(query: string, signal?: AbortSignal): Promise<LocationSuggestion[]> {
  const clean = query.trim().toLowerCase();
  if (!clean || clean.length < 2) {
    return [];
  }

  const results: LocationSuggestion[] = [];
  const seenKeys = new Set<string>();

  // 1. Check curated verified tech hubs and major localities first
  for (const hub of VERIFIED_TECH_HUBS) {
    const match =
      hub.name.toLowerCase().includes(clean) ||
      hub.displayName.toLowerCase().includes(clean) ||
      hub.value.toLowerCase().includes(clean) ||
      (hub.district && hub.district.toLowerCase().includes(clean)) ||
      (hub.state && hub.state.toLowerCase().includes(clean)) ||
      (hub.pincode && hub.pincode.startsWith(clean));

    if (match) {
      const key = hub.value.toLowerCase();
      if (!seenKeys.has(key)) {
        seenKeys.add(key);
        results.push(hub);
      }
    }
  }

  // 2. Query official postal records from Postal Pincode API
  try {
    const postalResults = await fetchFromPostalApi(query, signal);
    for (const item of postalResults) {
      const key = item.value.toLowerCase();
      if (!seenKeys.has(key)) {
        seenKeys.add(key);
        results.push(item);
      }
    }
  } catch {
    // If postal API is slow or throttled, attempt Nominatim
    try {
      const nominatimResults = await fetchFromNominatim(query, signal);
      for (const item of nominatimResults) {
        const key = item.value.toLowerCase();
        if (!seenKeys.has(key)) {
          seenKeys.add(key);
          results.push(item);
        }
      }
    } catch {
      // If network fails completely, local index and custom fallback remain available
    }
  }

  return results.slice(0, 10);
}
