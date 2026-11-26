export const serviceAreas = [
  ["LPU", "LPU Campus"],
  ["PHAGWARA", "Phagwara"],
  ["JALANDHAR", "Jalandhar"],
];

export const serviceTypes = [
  ["CAMPUS_SHUTTLE", "Campus shuttle"],
  ["E_RICKSHAW", "E-rickshaw"],
  ["AUTO_RICKSHAW", "Auto-rickshaw"],
  ["PUBLIC_BUS", "Public bus"],
  ["TRAIN", "Train"],
  ["OTHER", "Other"],
];

export const verificationStatuses = [
  ["PLANNED", "Planned"],
  ["PENDING_VERIFICATION", "Pending verification"],
  ["VERIFIED", "Verified"],
];

export const serviceStatuses = [
  ["ON_TIME", "On time"],
  ["DELAYED", "Delayed"],
  ["UNAVAILABLE", "Unavailable"],
  ["CANCELLED", "Cancelled"],
  ["UNKNOWN", "Unknown"],
  ["NOT_UPDATED", "Not updated"],
];

export const labelFor = (options, value) =>
  options.find(([optionValue]) => optionValue === value)?.[1] || value;
