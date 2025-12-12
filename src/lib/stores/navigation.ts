
import { writable } from 'svelte/store';

export const currentChapter = writable(1);
export const scrollProgress = writable(0);

export const chapters = [
  { id: 1, title: 'The Time Thief', subtitle: 'How Commutes Steal Your Life' },
  { id: 2, title: 'The Money Drain', subtitle: 'The True Cost of Getting to Work' },
  { id: 3, title: 'The Carbon Footprint', subtitle: 'Environmental Impact of Commuting' },
  { id: 4, title: 'Geography of Inequality', subtitle: 'Where You Live Matters' },
  { id: 5, title: 'Pennsylvania Counties Leading the Way', subtitle: 'Show What\'s Working' },
  { id: 6, title: 'Your Pennsylvania Choice', subtitle: 'Personal Action Calculator' },
  { id: 7, title: 'Productivity Paradox', subtitle: 'The Hidden Economic Cost' },
  { id: 8, title: 'Remote Work Revolution', subtitle: 'A New Way Forward' },
  { id: 9, title: 'Cities That Got It Right', subtitle: 'Success Stories' },
  { id: 10, title: 'Your Choice, Your Impact', subtitle: 'Take Action Today' }
];