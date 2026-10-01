/**
 * Weather mock data for Hyderabad
 * Structure matches standard public weather API schemas (e.g. Open-Meteo, IMD).
 */
export const initialWeatherData = {
  city: 'Hyderabad',
  state: 'Telangana',
  asOf: 'Updated today at 9:30 PM IST',
  station: 'Begumpet Airport Weather Observatory',
  current: {
    tempC: 28,
    feelsLikeC: 30,
    condition: 'Partly Cloudy',
    conditionCode: 'partly-cloudy',
    summary: 'Warm and humid with light westerly breeze. Low precipitation risk for the next 4 hours.',
    rainProbability: 15,
    humidity: 68,
    windSpeedKmh: 14,
    windDirection: 'WNW',
    pressureHpa: 1012,
    uvIndex: 4,
    uvLabel: 'Moderate',
    airQualityIndex: 76,
    airQualityLabel: 'Moderate',
    airQualityPollutant: 'PM2.5',
    visibilityKm: 6.0,
    tempHighC: 32,
    tempLowC: 23
  },
  hourly: [
    { time: '10 PM', tempC: 27, condition: 'Partly Cloudy', rainProb: 15 },
    { time: '11 PM', tempC: 26, condition: 'Clear Night', rainProb: 10 },
    { time: '12 AM', tempC: 25, condition: 'Clear Night', rainProb: 10 },
    { time: '01 AM', tempC: 24, condition: 'Cool Breeze', rainProb: 5 },
    { time: '06 AM', tempC: 23, condition: 'Mild Morning', rainProb: 10 },
    { time: '09 AM', tempC: 27, condition: 'Sunny Spells', rainProb: 15 },
    { time: '12 PM', tempC: 31, condition: 'Partly Cloudy', rainProb: 20 },
    { time: '03 PM', tempC: 32, condition: 'Scattered Clouds', rainProb: 30 }
  ],
  forecast: [
    {
      day: 'Today',
      date: 'Thu, Oct 1',
      condition: 'Partly Cloudy',
      tempMax: 32,
      tempMin: 23,
      rainProb: 20
    },
    {
      day: 'Tomorrow',
      date: 'Fri, Oct 2',
      condition: 'Afternoon Shower',
      tempMax: 31,
      tempMin: 23,
      rainProb: 45
    },
    {
      day: 'Saturday',
      date: 'Sat, Oct 3',
      condition: 'Scattered Clouds',
      tempMax: 30,
      tempMin: 22,
      rainProb: 30
    }
  ]
};
