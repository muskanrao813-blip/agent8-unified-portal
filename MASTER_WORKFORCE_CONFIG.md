# MASTER WORKFORCE KNOWLEDGE
## Authoritative Configuration (DO NOT CHANGE WITHOUT USER APPROVAL)
**Last Updated:** 2026-07-23  
**Status:** LOCKED - Source of Truth for all capacity calculations

---

## IN-HOUSE AI (6 Dieticians)
| Name | Slots per Day |
|------|--------------|
| Prachi More | 84 |
| Ambika Rode | 84 |
| Geeta Maggu | 84 |
| Gitanjali Malik Sachdeva | 84 |
| Chandni Sharma | 84 |
| Tejashree Thorat | 84 |
| **COHORT TOTAL** | **504** |

---

## IN-HOUSE OTHERS (2 Dieticians)
| Name | Slots per Day |
|------|--------------|
| Chaithra B | 14 |
| Shefali Dindorkar | 14 |
| **COHORT TOTAL** | **28** |

---

## IN-HOUSE MC (3 Dieticians + 1 Doctor)
### Dieticians:
| Name | Slots per Day |
|------|--------------|
| Sweta Naik | 14 |
| Divya Pandey | 14 |
| Trupti Nakar | 14 |
| **Dieticians Subtotal** | **42** |

### Doctor:
| Name | Slots per Day |
|------|--------------|
| Mekala Reddy | 4 |
| **Doctor Subtotal** | **4** |

| **COHORT TOTAL (MC)** | **46** |

---

## CONTRACTUAL (14 Dieticians)
| Name | Slots per Day |
|------|--------------|
| Hemlata Alawadhi | 22 |
| Ruchi Singh | 22 |
| Nisha Sharma | 22 |
| Hitesh Kumar | 22 |
| Priyadharshini R | 22 |
| Avani Mekala | 22 |
| Neha Suryawanshi | 22 |
| Homeshwar Mandawliya | 22 |
| Trapti Bhardwaj | 22 |
| Asra Jabeen | 22 |
| Midhat Zehra | 22 |
| Aparna Bhardwaj | 22 |
| Mital Bhadania | 22 |
| Shikha Singh | 22 |
| **COHORT TOTAL** | **308** |

---

## CAPACITY CALCULATION FORMULA
```
Total Daily Capacity = 504 + 28 + 46 + 308 = 886 slots/day

For date range:
Total Capacity = 886 × number_of_days_in_range
```

### Examples:
- July 1-23 (23 days): 886 × 23 = **20,378 slots**
- July 1-31 (31 days): 886 × 31 = **27,466 slots**
- Single day: 886 × 1 = **886 slots**

---

## APPOINTMENT STATUS FILTER (Locked)
**Include:** COM, BOOKED, ACT, WIC, RES  
**Exclude:** CAN (Cancelled), ANC  
**Data Source:** Trino f_appointmentflattable.appointmentstatus

---

## PROVIDER LIST (All 25)
**Total Providers:** 25 (24 dieticians + 1 doctor)
- IN-HOUSE AI: 6
- IN-HOUSE OTHERS: 2
- IN-HOUSE MC: 4 (3 dieticians + 1 doctor)
- CONTRACTUAL: 14

---

## NOTES
- This configuration is the DEFINITIVE source for all dashboard calculations
- Any changes to provider lists, slot allocations, or cohort assignments must update this file first
- Capacity calculations MUST use 886 slots/day as the baseline
- Appointment filters MUST always use: COM, BOOKED, ACT, WIC, RES
