## Introduction

This  document  describes  the  Standard  Operating  Procedures  (SOPs)  for  each  of  NovaMente's departments. SOPs define the repeatable processes that keep each team functioning predictably and at high quality. They reduce dependence on individual knowledge, make onboarding faster, and ensure that critical processes do not break down when key people are absent. Each department is responsible for maintaining the SOPs relevant to their function and for keeping them updated as processes evolve.

## Engineering

## Sprint Cycle

Engineering operates in two-week sprints. Sprint planning occurs on the first Monday of each sprint, with the Engineering Head and tech leads reviewing the backlog and committing to a sprint scope. Mid-sprint  check-ins  occur  on  Wednesday  of  the  first  week.  Sprint  reviews  are  held  on  the  last Friday of each sprint and include a demo of completed work to relevant stakeholders. Retrospectives follow immediately after the review and are facilitated by a rotating team member.

## Code Review

All code changes require review by at least one other engineer before merging. For changes to critical production systems, review by the tech lead is required. Reviewers are expected to respond within  one  working  day  of  a  review  request.  Code  reviews  should  be  constructive  and  specific, focusing  on  correctness,  maintainability,  security,  and  performance.  Approving  a  PR  without reviewing it substantively is not acceptable.

## Incident Response

When a production incident is detected, the on-call engineer is responsible for initial triage within 1 minutes of alert. The incident is classified by severity (P1 to P4) according to the severity matrix the Engineering handbook. P1 and P2 incidents trigger immediate escalation to the Engineering Head and, for client-facing outages, to the Commercial team. A post-incident review is required for all P1 and P2 incidents within 48 hours of resolution.

## Deployment

Deployments  to  production  occur  through  the  CI/CD  pipeline  and  require  passing  all  automated tests.  Deployments  during  business  hours  are  permitted  for  non-breaking  changes.  Breaking changes or major releases are deployed during low-traffic windows, defined as weekday evenings or weekend mornings, with prior notification to the Commercial team for client-facing changes.

## NovaMente Soluções Cognitivas

Document 18 - Standard Operating Procedures by Department

Version 1.0 · January 2025 · HR &amp; Culture Department

## Product &amp; Design

## Product Discovery

New  features  or  significant  changes  begin  with  a  discovery  phase,  during  which  the  product manager  and  UX  researcher  define  the  problem,  conduct  user  interviews,  review  analytics,  and explore  solution  directions.  Discovery  outputs  a  clear  problem  statement  and  a  set  of  design directions  to  be  evaluated.  The  discovery  phase  lasts  a  minimum  of  two  weeks  for  significant initiatives.

## PRD Process

Before moving into engineering, every feature requires a Product Requirements Document (PRD) approved  by  the  Product  Head  and  the  relevant  Engineering  tech  lead.  The  PRD  template  is maintained  in  the  knowledge  base  and  includes:  problem  statement,  user  stories,  acceptance criteria, out-of-scope items, dependencies, and open questions. Engineering may not begin work on a feature without an approved PRD.

## Design Handoff

Design handoff to engineering occurs through Figma, using the shared component library as the source of truth. Designers are responsible for annotating designs with interaction notes and edge cases  before  handoff.  A  handoff  review  session  between  the  designer  and  the  lead  engineer  is conducted for all significant features to resolve questions before implementation begins.

## Data &amp; AI

## Model Development

New  machine  learning  models  follow  a  structured  development  workflow:  problem  framing,  data exploration  and  validation,  feature  engineering,  model  training  and  evaluation,  bias  audit,  and production deployment. Each stage produces a documented artifact in the model registry. Models may not be deployed to production without completing the bias audit and performance benchmark review.

## Model Monitoring

All  production  models  are  monitored  weekly  for  performance  drift,  data  quality  issues,  and anomalous  outputs.  The  data  scientist  assigned  to  each  model  is  responsible  for  reviewing monitoring reports and escalating concerns to the Data &amp; AI Head when thresholds are exceeded. Models  that  fail  monitoring  thresholds  are  flagged  for  retraining  or  review  before  the  next deployment cycle.

## Data Pipeline Management

Data  pipelines  are  documented  in  the  data  catalog,  including  source,  transformation  logic, destination, refresh cadence, and data owner. Any change to a production pipeline requires review by  a  second  data  engineer  and  testing  in  the  staging  environment  before  deployment.  Pipeline failures trigger automated alerts to the on-call data engineer within five minutes of detection.

## Commercial

## Lead Management

All inbound leads are entered into the CRM within one working day of receipt and assigned to a sales representative by the Commercial Operations contact. Initial outreach to inbound leads must occur within 24 hours of assignment. Lead qualification follows the standard framework documented in  the  Commercial  playbook,  which  defines  criteria  for  advancing,  nurturing,  or  disqualifying  a prospect at each stage.

## Client Onboarding

Upon contract signature, the account is transitioned from Sales to Customer Success within three working days. The Customer Success manager conducts a kickoff call with the client within one week of contract signature, establishes the onboarding timeline, and provides access credentials and technical setup instructions. A 30-day check-in and a 90-day business review are mandatory for all new accounts.

## Renewal Management

Customer Success managers initiate renewal conversations 90 days before the contract end date. A renewal risk assessment is completed for each account at the 120-day mark, identifying accounts requiring additional attention. Renewals are tracked in the CRM and escalated to the Commercial Head if at risk of churning 60 or more days before expiry.

## HR &amp; Culture

## Recruitment Process

The end-to-end recruitment process follows the four-stage framework described in Document 08. The  HR  Manager  coordinates  each  stage,  tracks  candidate  progress  in  the  applicant  tracking system, and ensures that all candidates receive timely communications at each stage. Time-to-fill targets and candidate experience metrics are reported monthly to the COO.

## Onboarding

New employee onboarding follows the two-week program described in Document 04. The HR &amp; Culture  team  is  responsible  for  preparing  access,  equipment,  and  documentation  before  the employee's start date. Onboarding checklists are completed and filed in the HR system by the end of the employee's second week. A 30-day and 60-day check-in are scheduled by the HR Manager for all new hires.

## Performance Review Cycle

Semi-annual performance reviews occur in June and December. The HR &amp; Culture team distributes self-assessment  forms  three  weeks  before  the  review  window.  Managers  conduct  review conversations in the second week of the review window and submit evaluation forms to the HR system within five working days of the conversation. Salary adjustment decisions are communicated within two weeks of the review window closing.

## Finance &amp; Legal

## Payroll

Payroll is processed monthly. Payslips are distributed to employees by the last working day of each month. The Finance team collects all input data -overtime, commissions, expense reimbursements,  benefit  deductions  -  by  the  20th  of  each  month.  Errors  on  payslips  must  be reported to the Finance team within five working days of receipt; corrections are processed in the following month's cycle unless the error is material, in which case an off-cycle correction is issued.

## Contract Review

All contracts to which NovaMente is a party - client agreements, vendor contracts, NDAs, and employment agreements - require review and sign-off from the Legal Analyst before execution. Standard  agreements  below  defined  value  thresholds  use  pre-approved  templates  that  do  not require individual review. Contracts above the threshold or with non-standard terms require a full legal  review,  the  timeline  for  which  depends  on  complexity  and  is  agreed  in  advance  with  the requesting team.

## Budget Management

Annual budgets are set in November for the following calendar year, in coordination between the Finance Manager, department heads, and the COO. Quarterly budget reviews are conducted in March, June, and September. Department heads are responsible for monitoring their budget and flagging variances greater than 10% of the quarterly allocation to the Finance Manager as soon as they are identified.

## Marketing

## Campaign Planning

Marketing campaigns are planned on a monthly cycle aligned with the Commercial team's pipeline targets.  Campaign  briefs  are  produced  by  the  marketing  manager  by  the  15th  of  the  preceding month, reviewed by the Commercial Head, and approved before production begins. Post-campaign performance reviews are conducted within two weeks of campaign completion, with results shared in the weekly Commercial-Marketing alignment meeting.

## Content Production

All external content - blog posts, white papers, social media posts, email campaigns, and product materials - is reviewed for accuracy, brand consistency, and legal compliance before publication. Technical content is reviewed by a subject matter expert from the relevant department. Content featuring  client  references  or  case  studies  requires  written  approval  from  the  client  before publication.

## Event Management

Industry events attended or hosted by NovaMente are planned a minimum of six weeks in advance. Event  briefs,  budgets,  and  logistics  are  coordinated  by  the  Marketing  team  with  input  from  the relevant department heads. Post-event reports, including lead capture, brand exposure metrics, and follow-up actions, are produced within one week of each event.