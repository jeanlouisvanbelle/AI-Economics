import numpy as np
import matplotlib.pyplot as plt

def run_simulation(t_max=10.0, steps=2000):
    t = np.linspace(0, t_max, steps)
    dt = t[1] - t[0]

    # -------------------------------------------------------------
    # 1. DEMOGRAPHIC PARAMETERS (Bottom-Heavy Professional Pyramid)
    # -------------------------------------------------------------
    S0 = 50.0           # Senior Experts / Partners (FTEs)
    J0 = 100.0          # Junior Associates / Analysts (FTEs)
    
    gamma_0 = 0.12      # Senior annual turnover/retirement (12%/yr -> 6 exits/yr)
    delta_j = 0.15      # Junior career attrition/external exit (15%/yr)
    H_target = 38.0     # Sustainable annual hiring rate
    promo_rate = 0.20   # 20% conversion from final-year cohort (~6 FTEs/yr)
    
    # -------------------------------------------------------------
    # 2. COMPLEXITY PARAMETERS (Option A: Calibrated 3:1 Safety Margin)
    # -------------------------------------------------------------
    C0 = 17.0           # Baseline complexity (matched to 50 seniors)
    r_unmanaged = 0.12  # Unmanaged AI sprawl compounding rate (12%/yr)
    r_managed = 0.08    # Refactored growth rate under Playbook governance
    C_max = 24.0        # Refactored complexity ceiling (well below S = 50)
    
    # -------------------------------------------------------------
    # SCENARIO A: STATUS QUO (Hiring Freeze Phased in Year 1)
    # -------------------------------------------------------------
    freeze_ramp = np.clip(1.0 - t / 1.0, 0.0, 1.0)
    H_j_sq = H_target * freeze_ramp
    
    c1_sq = np.zeros(steps)
    c2_sq = np.zeros(steps)
    c3_sq = np.zeros(steps)
    J_sq = np.zeros(steps)
    S_sq = np.zeros(steps)
    
    c1_sq[0] = 38.0
    c2_sq[0] = 32.0
    c3_sq[0] = 30.0
    J_sq[0] = 100.0
    S_sq[0] = S0
    C_sq = C0 * np.exp(r_unmanaged * t)
    
    for i in range(1, steps):
        dc1 = (H_j_sq[i-1] - c1_sq[i-1] - delta_j * c1_sq[i-1]) * dt
        dc2 = (c1_sq[i-1] - c2_sq[i-1] - delta_j * c2_sq[i-1]) * dt
        dc3 = (c2_sq[i-1] - c3_sq[i-1] - delta_j * c3_sq[i-1]) * dt
        
        c1_sq[i] = max(0.0, c1_sq[i-1] + dc1)
        c2_sq[i] = max(0.0, c2_sq[i-1] + dc2)
        c3_sq[i] = max(0.0, c3_sq[i-1] + dc3)
        
        J_sq[i] = c1_sq[i] + c2_sq[i] + c3_sq[i]
        graduation = promo_rate * c3_sq[i-1]
        
        # Senior fatigue accelerates as the junior buffer drains
        junior_deficit = max(0.0, (J0 - J_sq[i]) / J0)
        gamma_eff = gamma_0 + 0.06 * junior_deficit
        
        decay_s = -gamma_eff * S_sq[i-1] * dt
        S_sq[i] = max(1.0, S_sq[i-1] + decay_s + graduation * dt)

    # -------------------------------------------------------------
    # SCENARIO B: PLAYBOOK DYNAMIC EQUILIBRIUM
    # -------------------------------------------------------------
    J_rn = np.full(steps, J0)
    S_rn = np.full(steps, S0)
    
    C_rn = np.zeros(steps)
    C_rn[0] = C0
    for i in range(1, steps):
        dC = r_managed * C_rn[i-1] * (1.0 - C_rn[i-1] / C_max) * dt
        C_rn[i] = C_rn[i-1] + dC

    return t, S_sq, J_sq, C_sq, S_rn, J_rn, C_rn

if __name__ == '__main__':
    t, S_sq, J_sq, C_sq, S_rn, J_rn, C_rn = run_simulation()

    # Calculate exact crossover point t*
    cross_idx = np.where(C_sq >= S_sq)[0]
    t_star = t[cross_idx[0]] if len(cross_idx) > 0 else None
    if t_star:
        print(f"--> Success: Critical System Black Box Threshold t* = {t_star:.2f} Years")

    # -------------------------------------------------------------
    # FIGURE 1: WORKFORCE DEMOGRAPHICS & STAFFING MIX
    # -------------------------------------------------------------
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(9, 8), dpi=200)

    ax1.plot(t, J_sq, 'r--', lw=2.2, label='Junior Stock J(t) (Status Quo: 3-Year Depletion)')
    ax1.plot(t, S_sq, 'r-', lw=2.2, label='Senior Stock S(t) (Status Quo Atrophy)')
    ax1.plot(t, J_rn, 'g--', lw=2.2, label='Junior Stock J(t) (Playbook Sustained Base: 100 FTEs)')
    ax1.plot(t, S_rn, 'g-', lw=2.2, label='Senior Stock S(t) (Playbook Anchored Core: 50 FTEs)')
    ax1.set_title('Enterprise Human Capital: Bottom-Heavy Pyramid Demographics', fontweight='bold', fontsize=11)
    ax1.set_ylabel('Workforce Stock (FTEs)', fontsize=10)
    ax1.set_ylim(-5, 115)
    ax1.legend(loc='center right', frameon=True)
    ax1.grid(True, alpha=0.3)

    mix_sq = J_sq / (S_sq + J_sq) * 100.0
    mix_rn = J_rn / (S_rn + J_rn) * 100.0
    ax2.plot(t, mix_sq, 'r-', lw=2.2, label='Junior Ratio (Status Quo: Career Runway Collapse)')
    ax2.plot(t, mix_rn, 'g-', lw=2.2, label='Junior Ratio (Playbook: Balanced 67% Share)')
    ax2.set_title('Staffing Composition: Junior Talent Share of Total Workforce', fontweight='bold', fontsize=11)
    ax2.set_xlabel('Years', fontsize=10)
    ax2.set_ylabel('Junior Share of Workforce (%)', fontsize=10)
    ax2.set_ylim(-5, 75)
    ax2.legend(loc='center right', frameon=True)
    ax2.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig('figure1_workforce_demographics_v6.png', bbox_inches='tight')
    plt.close()

    # -------------------------------------------------------------
    # FIGURE 2: THE SYSTEM BLACK BOX (CAPABILITY VS. BOUNDED COMPLEXITY)
    # -------------------------------------------------------------
    plt.figure(figsize=(9, 5.5), dpi=200)
    plt.plot(t, S_sq, 'r-', lw=2.5, label='Senior Expertise S(t) (Status Quo Decay)')
    plt.plot(t, C_sq, 'r--', lw=2.0, label='AI Complexity C(t) (Unmanaged Sprawl: 12% Compound)')
    plt.plot(t, S_rn, 'g-', lw=2.5, label='Senior Expertise S(t) (Playbook Sustained Core: 50 FTEs)')
    plt.plot(t, C_rn, 'b--', lw=2.0, label='AI Complexity C(t) (Playbook Bounded Refactoring)')

    if t_star:
        idx = cross_idx[0]
        plt.scatter(t_star, S_sq[idx], color='darkred', s=100, zorder=5)
        plt.axvline(t_star, color='darkred', linestyle=':', lw=1.5)
        plt.text(t_star + 0.15, S_sq[idx] + 3, f'Critical Threshold\nt* = {t_star:.2f} Years', 
                 color='darkred', fontweight='bold', fontsize=9.5)
        plt.fill_between(t[t >= t_star], S_sq[t >= t_star], C_sq[t >= t_star], color='red', alpha=0.08)

    plt.title('The System Black Box Model: Human Expertise vs. System Complexity', fontweight='bold', fontsize=12)
    plt.xlabel('Simulation Time Horizon (Years)', fontsize=10)
    plt.ylabel('Enterprise Units (Headcount / Complexity)', fontsize=10)
    plt.xlim(0, 10)
    plt.ylim(0, 65)
    plt.legend(loc='upper right', frameon=True)
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig('figure2_system_black_box_v6.png', bbox_inches='tight')
    plt.close()

    # -------------------------------------------------------------
    # FIGURE 3: SYSTEMIC OPERATIONAL FRAGILITY INDEX
    # -------------------------------------------------------------
    plt.figure(figsize=(9, 5.5), dpi=200)
    frag_sq = C_sq / S_sq
    frag_rn = C_rn / S_rn

    plt.plot(t, frag_sq, 'r-', lw=2.5, label='Fragility C(t)/S(t) (Status Quo Defection)')
    plt.plot(t, frag_rn, 'g-', lw=2.5, label='Fragility C(t)/S(t) (Playbook Dynamic Equilibrium)')
    plt.axhline(1.0, color='black', linestyle=':', lw=1.5, label='Audit Boundary Threshold (C = S)')

    plt.fill_between(t, 1.0, np.maximum(1.0, frag_sq), color='red', alpha=0.1, label='Zone of Blind Reliance')
    plt.title('Systemic Operational Fragility: Technical Debt Relative to Senior Oversight', fontweight='bold', fontsize=12)
    plt.xlabel('Simulation Time Horizon (Years)', fontsize=10)
    plt.ylabel('Fragility Ratio (Complexity per Senior FTE)', fontsize=10)
    plt.xlim(0, 10)
    plt.ylim(0.2, 4.0)
    plt.legend(loc='upper left', frameon=True)
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig('figure3_operational_fragility_v6.png', bbox_inches='tight')
    plt.close()

    print("--> All 3 figures generated and saved successfully.")