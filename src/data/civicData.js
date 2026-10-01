/**
 * Civic updates and public notices mock data for Hyderabad
 * Realistic public notices from municipal and utility departments.
 */
export const civicData = [
  {
    id: 'civic-1',
    source: 'HMWS&SB (Water Supply Board)',
    departmentBadge: 'Water Supply',
    title: 'Scheduled Water Supply Shutdown for Pipeline Interconnection',
    date: 'Oct 1, 2026 • 08:30 AM',
    status: 'Scheduled Maintenance',
    urgency: 'medium',
    affectedAreas: 'Jubilee Hills (Phases 1-3), Banjara Hills (Roads 10-14), and Venkatagiri',
    summary: 'Water supply will be temporarily interrupted for 16 hours starting Friday 6:00 AM due to Krishna Phase-3 junction pipeline maintenance. Citizens in affected divisions are advised to store adequate water in advance.',
    officialReference: 'HMWS/PR/2026/1042',
    actionNote: 'Tanker water booking helpline: 155313'
  },
  {
    id: 'civic-2',
    source: 'Hyderabad Traffic Police',
    departmentBadge: 'Traffic Advisory',
    title: 'Nightly Resurfacing on PVNR Expressway (Pillars 110 to 175)',
    date: 'Oct 1, 2026 • 02:15 PM',
    status: 'Traffic Advisory',
    urgency: 'low',
    affectedAreas: 'PVNR Expressway (Airport Corridor, Mehdipatnam toward Aramgarh)',
    summary: 'One lane of the elevated expressway will be restricted for micro-surfacing works between 11:30 PM and 5:00 AM. Airport-bound passengers are advised to allow an extra 15 minutes or use the below-grade NH-44 route.',
    officialReference: 'HTP/TRAF/ADV/489',
    actionNote: 'Traffic control room: 040-27852482'
  },
  {
    id: 'civic-3',
    source: 'GHMC (Municipal Corporation)',
    departmentBadge: 'Public Sanitation',
    title: 'Intensive Pre-Winter Silt Clearance in Nalhas and Inlets',
    date: 'Sep 30, 2026 • 05:00 PM',
    status: 'Civic Notice',
    urgency: 'low',
    affectedAreas: 'Khairatabad, Musheerabad, and Amberpet circles',
    summary: 'Special emergency teams deployed for desilting tertiary stormwater drains. Residents are urged not to discard solid plastic waste or construction debris into road gullies and open vents.',
    officialReference: 'GHMC/ENG/DRN/2026',
    actionNote: 'Grievance app: MyGHMC or call 040-21111111'
  },
  {
    id: 'civic-4',
    source: 'Hyderabad Metro Rail (HMRL) & TGSRTC',
    departmentBadge: 'Public Transit',
    title: 'Extension of Night Feeder Bus Frequency from Raidurg Metro',
    date: 'Sep 29, 2026 • 11:00 AM',
    status: 'Service Enhancement',
    urgency: 'info',
    affectedAreas: 'Raidurg, Financial District, Gachibowli Outer Ring Road',
    summary: 'TGSRTC has introduced six additional low-floor electric feeder shuttles running every 8 minutes between Raidurg Metro Station and Waverock/GAR SEZ between 9:30 PM and 11:45 PM.',
    officialReference: 'HMRL/FEEDER/771',
    actionNote: 'Metro smart cards accepted on all feeder shuttles'
  }
];
