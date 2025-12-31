"""
Gate Controller Module
State machine for person detection gate control
(No MQTT - hardware not deployed yet)
"""
import time


class GateController:
    """
    Gate Controller with state machine
    
    States: CLOSED, OPEN
    Rules:
    - Person detected (conf >= 0.7) for 10 seconds -> OPEN
    - No person (conf < 0.7) -> CLOSE immediately
    """
    
    # State constants
    STATE_CLOSED = "CLOSED"
    STATE_OPEN = "OPEN"
    
    # Timing constants (seconds)
    OPEN_DELAY = 10.0     # Time person must be present to open gate (10s countdown)
    CLOSE_DELAY = 0.5     # Quick close when no person detected
    
    def __init__(self):
        """Initialize gate controller"""
        self.state = self.STATE_CLOSED
        self.person_present_start = None  # When person first detected
        self.person_absent_start = None   # When person first disappeared
        
        print(f"[Gate] Initialized - State: {self.state}")
    
    def update(self, person_detected: bool) -> str:
        """
        Update gate state based on person detection
        
        Args:
            person_detected: True if person is detected with confidence >= 0.7
            
        Returns:
            Current gate state (CLOSED or OPEN)
        """
        current_time = time.time()
        
        if person_detected:
            # Person is present with high confidence
            self.person_absent_start = None  # Reset absence timer
            
            if self.person_present_start is None:
                # First detection
                self.person_present_start = current_time
            
            # Check if person has been present long enough to open gate
            if self.state == self.STATE_CLOSED:
                elapsed = current_time - self.person_present_start
                if elapsed >= self.OPEN_DELAY:
                    self._open_gate()
        else:
            # No person detected or low confidence
            self.person_present_start = None  # Reset presence timer
            
            if self.person_absent_start is None:
                # First absence detection
                self.person_absent_start = current_time
            
            # Close gate quickly when no person
            if self.state == self.STATE_OPEN:
                elapsed = current_time - self.person_absent_start
                if elapsed >= self.CLOSE_DELAY:
                    self._close_gate()
        
        return self.state
    
    def _open_gate(self):
        """Open the gate"""
        if self.state != self.STATE_OPEN:
            self.state = self.STATE_OPEN
            print(f"[Gate] IN -> OPEN 🚪")
            return True
        return False
    
    def _close_gate(self):
        """Close the gate"""
        if self.state != self.STATE_CLOSED:
            self.state = self.STATE_CLOSED
            print(f"[Gate] IN -> CLOSED 🔒")
            return True
        return False
    
    def force_open(self):
        """Force open gate (manual control)"""
        self.person_present_start = time.time() - self.OPEN_DELAY  # Instant open
        return self._open_gate()
    
    def force_close(self):
        """Force close gate (manual control)"""
        self.person_absent_start = time.time() - self.CLOSE_DELAY  # Instant close
        return self._close_gate()
    
    def get_status(self) -> dict:
        """Get current gate status"""
        return {
            "state": self.state,
            "person_present_duration": (
                time.time() - self.person_present_start 
                if self.person_present_start else 0
            ),
            "person_absent_duration": (
                time.time() - self.person_absent_start 
                if self.person_absent_start else 0
            )
        }
    
    def cleanup(self):
        """Cleanup (no MQTT, just print)"""
        print("[Gate] Controller cleanup complete")


# Global instance for easy import
gate_controller = GateController()


if __name__ == "__main__":
    # Test the gate controller
    print("\n=== GateController Test ===")
    gc = GateController()
    
    print("\nSimulating person detection for 11 seconds...")
    for i in range(110):  # 11 seconds
        state = gc.update(person_detected=True)
        print(f"  [{i/10:.1f}s] Person: YES | Gate: {state}")
        time.sleep(0.1)
    
    print("\nSimulating no person for 2 seconds...")
    for i in range(20):  # 2 seconds
        state = gc.update(person_detected=False)
        print(f"  [{i/10:.1f}s] Person: NO  | Gate: {state}")
        time.sleep(0.1)
    
    gc.cleanup()
    print("\n=== Test Complete ===")
