export type AuthUser = {
    id: number;
    username: string;
    organization_id: string;
    organization_name: string;
  };
  
  export type LoginResponse = {
    token: string;
    user: AuthUser;
  };
  
  export type ReconciliationException = {
    id: number;
    organization_id: string;
    location_id: string | null;
    record_id: string;
    reason_code: string;
    reason: string;
    system_a_record_id: string;
    system_b_entry_ids: string[];
    evidence: Record<string, unknown>;
    created_at: string;
  };
  
  export type ExceptionListResponse = {
    count: number;
    results: ReconciliationException[];
  };
  
  export type ExceptionFilters = {
    reasonCode?: string;
    recordId?: string;
    locationId?: string;
  };

  export type ExceptionQuestionRequest = {
    question: string;
  };
  
  export type ExceptionQuestionResponse = {
    answer: string;
    citations: number[];
    supported: boolean;
  };