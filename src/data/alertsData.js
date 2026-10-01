/**
 * Weather & Civic Alerts mock data for Hyderabad
 * Provides both normal (no alerts) and active warning states for testing.
 */
export const alertsData = {
  sources: [
    'India Meteorological Department (IMD) Hyderabad',
    'Telangana State Development Planning Society (TSDPS)',
    'Disaster Response and Fire Services (GHMC/HYDRAA)'
  ],
  normalState: {
    hasAlert: false,
    severity: 'normal', // 'normal' | 'advisory' | 'warning' | 'severe'
    badge: 'Normal Conditions',
    headline: 'No Active Emergency Alerts',
    description: 'Civic services and weather conditions across the Greater Hyderabad Municipal Corporation (GHMC) limits are operating normally. No weather warnings in effect.',
    lastVerified: 'Checked 8 minutes ago',
    contacts: [
      { name: 'GHMC Central Helpline', number: '040-21111111' },
      { name: 'Emergency Medical (Ambulance)', number: '108' }
    ]
  },
  activeWarningState: {
    hasAlert: true,
    severity: 'warning',
    badge: 'Yellow Alert • Heavy Rain Warning',
    headline: 'Heavy Rainfall & Waterlogging Advisory',
    issuedBy: 'IMD Hyderabad & Disaster Management Cell',
    validFrom: 'Today, 04:00 PM',
    validUntil: 'Tonight, 11:30 PM',
    summary: 'Localized thunderstorm accompanied by gusty winds (30-40 km/h) and intense rain spells (40-65 mm) expected across parts of western and central Hyderabad.',
    affectedZones: [
      'Serilingampally / Hitec City',
      'Khairatabad & Banjara Hills',
      'Kukatpally & Miyapur',
      'Secunderabad Cantonment'
    ],
    guidelines: [
      'Avoid parking vehicles beneath old trees or fragile tin sheds.',
      'Check traffic police road status before using low-lying railway underpasses (e.g. Malakpet, Begumpet).',
      'Pedestrians are requested to stay clear of storm water drain grates and open manholes.'
    ],
    emergencyContacts: [
      { label: 'GHMC Monsoon Emergency Cell', tel: '040-21111111' },
      { label: 'HYDRAA Disaster Response', tel: '040-29560521' },
      { label: 'Hyderabad Traffic Police Control', tel: '040-27852482' },
      { label: 'State Emergency Operation Centre', tel: '1070' }
    ]
  }
};
