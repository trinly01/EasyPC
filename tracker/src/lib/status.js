// Ordered journey used for the timeline UI. Terminal/exceptional statuses
// (cancelled, unclaimed) render separately.
export const JOURNEY = [
  "registered",
  "awaiting_assessment",
  "assessing",
  "awaiting_approval",
  "in_repair",
  "testing",
  "ready_for_release",
  "released",
]

export const STATUS_LABEL = {
  registered: "Registered",
  awaiting_assessment: "Awaiting Assessment",
  assessing: "Assessing",
  awaiting_approval: "Awaiting Approval",
  in_repair: "In Repair",
  testing: "Testing",
  ready_for_release: "Ready for Pickup",
  released: "Released",
  unclaimed: "Unclaimed",
  cancelled: "Cancelled",
}

export const STATUS_DESC = {
  registered: "Your unit is logged at the service center.",
  awaiting_assessment: "Waiting in queue for a technician to assess.",
  assessing: "A technician is diagnosing your unit.",
  awaiting_approval: "Findings are ready — waiting for your approval to proceed.",
  in_repair: "Our technician is working on your unit.",
  testing: "Repair done — running final diagnostics.",
  ready_for_release: "Passed testing. Ready for pickup — bring your Job Order No. and a valid ID.",
  released: "Unit released. Thank you for choosing EasyPC!",
  unclaimed: "Unit unclaimed. Please contact the store.",
  cancelled: "This work order was cancelled.",
}

export function statusVariant(status) {
  if (status === "released") return "default"
  if (status === "cancelled" || status === "unclaimed") return "destructive"
  if (status === "ready_for_release" || status === "testing") return "warning"
  return "secondary"
}
