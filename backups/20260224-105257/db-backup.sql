--
-- PostgreSQL database dump
--

\restrict 00gEnQyT8VHgMpnfro5yBaJyxwZ8ahFyg3EcTCWzFoI0ELmjbJfdlAfGiZHM83Y

-- Dumped from database version 15.15 (Debian 15.15-1.pgdg13+1)
-- Dumped by pg_dump version 15.15 (Debian 15.15-1.pgdg13+1)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: public; Type: SCHEMA; Schema: -; Owner: awards_user
--

-- *not* creating schema, since initdb creates it


ALTER SCHEMA public OWNER TO awards_user;

--
-- Name: SCHEMA public; Type: COMMENT; Schema: -; Owner: awards_user
--

COMMENT ON SCHEMA public IS '';


--
-- Name: cyclestatus; Type: TYPE; Schema: public; Owner: awards_user
--

CREATE TYPE public.cyclestatus AS ENUM (
    'DRAFT',
    'OPEN',
    'CLOSED',
    'FINALIZED',
    'ACTIVE'
);


ALTER TYPE public.cyclestatus OWNER TO awards_user;

--
-- Name: userrole; Type: TYPE; Schema: public; Owner: awards_user
--

CREATE TYPE public.userrole AS ENUM (
    'HR',
    'MANAGER',
    'EMPLOYEE',
    'PANEL',
    'SUPER_ADMIN'
);


ALTER TYPE public.userrole OWNER TO awards_user;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: alembic_version; Type: TABLE; Schema: public; Owner: awards_user
--

CREATE TABLE public.alembic_version (
    version_num character varying(32) NOT NULL
);


ALTER TABLE public.alembic_version OWNER TO awards_user;

--
-- Name: award_types; Type: TABLE; Schema: public; Owner: awards_user
--

CREATE TABLE public.award_types (
    id uuid NOT NULL,
    code character varying(100) NOT NULL,
    label character varying(150) NOT NULL,
    description character varying(500),
    is_active boolean DEFAULT true NOT NULL,
    created_at timestamp without time zone DEFAULT now() NOT NULL,
    updated_at timestamp without time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.award_types OWNER TO awards_user;

--
-- Name: awards; Type: TABLE; Schema: public; Owner: awards_user
--

CREATE TABLE public.awards (
    id uuid NOT NULL,
    cycle_id uuid NOT NULL,
    nomination_id uuid NOT NULL,
    winner_id uuid NOT NULL,
    rank integer,
    is_active boolean,
    created_at timestamp without time zone,
    finalized_at timestamp without time zone,
    comment character varying(1000),
    updated_at timestamp without time zone,
    award_type_id uuid,
    award_type_label character varying(100)
);


ALTER TABLE public.awards OWNER TO awards_user;

--
-- Name: cycles; Type: TABLE; Schema: public; Owner: awards_user
--

CREATE TABLE public.cycles (
    id uuid NOT NULL,
    name character varying(150) NOT NULL,
    description character varying(500),
    quarter character varying(20) NOT NULL,
    year integer NOT NULL,
    start_date date NOT NULL,
    end_date date NOT NULL,
    status public.cyclestatus NOT NULL,
    is_active boolean,
    created_at timestamp without time zone,
    updated_at timestamp without time zone,
    award_type_id uuid
);


ALTER TABLE public.cycles OWNER TO awards_user;

--
-- Name: form_answers; Type: TABLE; Schema: public; Owner: awards_user
--

CREATE TABLE public.form_answers (
    id uuid NOT NULL,
    nomination_id uuid NOT NULL,
    field_key character varying(100) NOT NULL,
    value jsonb NOT NULL,
    attachment character varying(500)
);


ALTER TABLE public.form_answers OWNER TO awards_user;

--
-- Name: form_fields; Type: TABLE; Schema: public; Owner: awards_user
--

CREATE TABLE public.form_fields (
    id uuid NOT NULL,
    form_id uuid NOT NULL,
    label character varying(255) NOT NULL,
    field_key character varying(100) NOT NULL,
    field_type character varying(50) NOT NULL,
    is_required boolean,
    order_index integer,
    options jsonb,
    ui_schema jsonb,
    validation jsonb,
    allow_file_upload boolean
);


ALTER TABLE public.form_fields OWNER TO awards_user;

--
-- Name: forms; Type: TABLE; Schema: public; Owner: awards_user
--

CREATE TABLE public.forms (
    id uuid NOT NULL,
    name character varying(150) NOT NULL,
    description character varying(500),
    is_active boolean,
    created_at timestamp without time zone,
    category character varying(100)
);


ALTER TABLE public.forms OWNER TO awards_user;

--
-- Name: nominations; Type: TABLE; Schema: public; Owner: awards_user
--

CREATE TABLE public.nominations (
    id uuid NOT NULL,
    cycle_id uuid NOT NULL,
    form_id uuid NOT NULL,
    nominee_id uuid,
    nominated_by_id uuid,
    status character varying(50),
    submitted_at timestamp without time zone,
    created_at timestamp without time zone,
    updated_at timestamp without time zone
);


ALTER TABLE public.nominations OWNER TO awards_user;

--
-- Name: panel_assignments; Type: TABLE; Schema: public; Owner: awards_user
--

CREATE TABLE public.panel_assignments (
    id uuid NOT NULL,
    nomination_id uuid NOT NULL,
    panel_id uuid NOT NULL,
    assigned_by uuid NOT NULL,
    status character varying(20) NOT NULL,
    assigned_at timestamp with time zone DEFAULT now() NOT NULL,
    completed_at timestamp with time zone
);


ALTER TABLE public.panel_assignments OWNER TO awards_user;

--
-- Name: panel_members; Type: TABLE; Schema: public; Owner: awards_user
--

CREATE TABLE public.panel_members (
    id uuid NOT NULL,
    panel_id uuid NOT NULL,
    user_id uuid NOT NULL,
    role character varying(20) NOT NULL,
    created_at timestamp with time zone DEFAULT now()
);


ALTER TABLE public.panel_members OWNER TO awards_user;

--
-- Name: panel_reviews; Type: TABLE; Schema: public; Owner: awards_user
--

CREATE TABLE public.panel_reviews (
    id uuid NOT NULL,
    panel_assignment_id uuid NOT NULL,
    panel_member_id uuid NOT NULL,
    panel_task_id uuid NOT NULL,
    score integer NOT NULL,
    comment character varying,
    reviewed_at timestamp with time zone DEFAULT now()
);


ALTER TABLE public.panel_reviews OWNER TO awards_user;

--
-- Name: panel_tasks; Type: TABLE; Schema: public; Owner: awards_user
--

CREATE TABLE public.panel_tasks (
    id uuid NOT NULL,
    panel_id uuid NOT NULL,
    title character varying(255) NOT NULL,
    description character varying,
    max_score integer NOT NULL,
    order_index integer NOT NULL,
    is_required boolean,
    criteria_field_id uuid
);


ALTER TABLE public.panel_tasks OWNER TO awards_user;

--
-- Name: panels; Type: TABLE; Schema: public; Owner: awards_user
--

CREATE TABLE public.panels (
    id uuid NOT NULL,
    name character varying(255) NOT NULL,
    description character varying,
    is_active boolean,
    created_at timestamp with time zone DEFAULT now()
);


ALTER TABLE public.panels OWNER TO awards_user;

--
-- Name: security_questions; Type: TABLE; Schema: public; Owner: awards_user
--

CREATE TABLE public.security_questions (
    id uuid NOT NULL,
    user_id uuid,
    question character varying(255) NOT NULL,
    answer_hash character varying(255) NOT NULL
);


ALTER TABLE public.security_questions OWNER TO awards_user;

--
-- Name: users; Type: TABLE; Schema: public; Owner: awards_user
--

CREATE TABLE public.users (
    id uuid NOT NULL,
    employee_code character varying(50),
    name character varying(150) NOT NULL,
    email character varying(150) NOT NULL,
    password_hash character varying(255) NOT NULL,
    role public.userrole NOT NULL,
    is_active boolean,
    delete_requested_at timestamp without time zone,
    deleted_at timestamp without time zone,
    profile_image character varying(255),
    created_at timestamp without time zone
);


ALTER TABLE public.users OWNER TO awards_user;

--
-- Data for Name: alembic_version; Type: TABLE DATA; Schema: public; Owner: awards_user
--

COPY public.alembic_version (version_num) FROM stdin;
a08c43a46191
\.


--
-- Data for Name: award_types; Type: TABLE DATA; Schema: public; Owner: awards_user
--

COPY public.award_types (id, code, label, description, is_active, created_at, updated_at) FROM stdin;
ca93677b-8541-40ea-87a5-05f14c328724	EXCELLENCE	Excellence Award	For outstanding performance and achievements.	t	2026-02-24 05:20:24.596039	2026-02-24 05:20:24.596041
996adb68-2b04-4de8-afe0-01545aeaee20	PEER	Peer Recognition	Nominated by colleagues for teamwork and support.	t	2026-02-24 05:20:24.598171	2026-02-24 05:20:24.598172
f94a9212-6eb2-4dec-9a5e-aedf9507c16d	INNOVATION	Innovation Award	For creative solutions and process improvements.	t	2026-02-24 05:20:24.598997	2026-02-24 05:20:24.598999
\.


--
-- Data for Name: awards; Type: TABLE DATA; Schema: public; Owner: awards_user
--

COPY public.awards (id, cycle_id, nomination_id, winner_id, rank, is_active, created_at, finalized_at, comment, updated_at, award_type_id, award_type_label) FROM stdin;
\.


--
-- Data for Name: cycles; Type: TABLE DATA; Schema: public; Owner: awards_user
--

COPY public.cycles (id, name, description, quarter, year, start_date, end_date, status, is_active, created_at, updated_at, award_type_id) FROM stdin;
42273e56-2e1c-4f30-91b6-c6de2050798d	Orchestration Cycle 1771474477158	Orchestration Flow Test	Q1	2026	2026-01-01	2026-03-31	DRAFT	t	2026-02-19 04:14:40.102515	2026-02-19 04:14:40.10252	\N
dea2b80b-08bc-4d1f-8f5a-aea8cd4629b0	Orchestration Cycle 1771474910941	Orchestration Flow Test	Q1	2026	2026-01-01	2026-03-31	DRAFT	t	2026-02-19 04:21:53.840075	2026-02-19 04:21:53.840079	\N
c47042a8-097f-40d6-8150-25b0f021c167	Orchestration Cycle 1771474969029	Orchestration Flow Test	Q1	2026	2026-01-01	2026-03-31	DRAFT	t	2026-02-19 04:22:51.794457	2026-02-19 04:22:51.794462	\N
2df23d6a-913c-4cdb-a56d-774d9d249068	Manual Test Cycle		Q1	2026	2024-01-01	2024-12-31	DRAFT	t	2026-02-19 04:24:01.332375	2026-02-19 04:24:01.332382	\N
88ea8719-8874-4c2d-97b9-a2bb310fd718	Manual Test Cycle		Q1	2024	2024-01-01	2024-12-31	DRAFT	t	2026-02-19 04:24:51.238028	2026-02-19 04:24:51.238036	\N
6f886c71-f9e4-4086-bf71-94d994b098ae	Manual Test Cycle Final 2		Q1	2026	2026-01-01	2026-03-31	DRAFT	t	2026-02-19 04:27:43.928265	2026-02-19 04:27:43.92901	\N
b63357fb-da8f-4777-85e4-dd833a56fff6	Manual Test Cycle		Q1	2026	2026-01-01	2026-03-31	DRAFT	t	2026-02-19 04:30:14.1226	2026-02-19 04:30:14.122607	\N
658efe76-2ae5-4ced-bd81-724e78a18283	Orchestration Cycle 1771476254567	Orchestration Flow Test	Q1	2026	2026-01-01	2026-03-31	DRAFT	t	2026-02-19 04:44:16.311087	2026-02-19 04:44:16.311089	\N
f0538f2d-c262-4488-8360-8a91b8829a0c	Orchestration Cycle 1771476314394	Orchestration Flow Test	Q1	2026	2026-01-01	2026-03-31	DRAFT	t	2026-02-19 04:45:16.28936	2026-02-19 04:45:16.289366	\N
5a700242-12b1-4b2c-a737-eace49bfad8c	Orchestration Cycle 1771476778457	Orchestration Flow Test	Q1	2026	2026-01-01	2026-03-31	DRAFT	t	2026-02-19 04:52:59.66308	2026-02-19 04:52:59.663083	\N
bcf721c2-db15-4114-b28f-c1654307afbe	Orchestration Cycle 1771476809742	Orchestration Flow Test	Q1	2026	2026-01-01	2026-03-31	DRAFT	t	2026-02-19 04:53:31.734627	2026-02-19 04:53:31.734715	\N
df515c16-5f57-430d-ab9a-664db643b436	Orchestration Cycle 1771477269053	Orchestration Flow Test	Q1	2026	2026-01-01	2026-03-31	DRAFT	t	2026-02-19 05:01:12.608229	2026-02-19 05:01:12.608234	\N
eb542b38-06c8-4835-ac44-be03f1f144a7	Orchestration Cycle 1771477409162	Orchestration Flow Test	Q1	2026	2026-01-01	2026-03-31	OPEN	t	2026-02-19 05:03:32.670032	2026-02-19 05:03:32.685686	\N
b8109e9b-e2a4-4fee-9229-71cf2051befd	Orchestration Cycle 1771477660404	Orchestration Flow Test	Q1	2026	2026-01-01	2026-03-31	OPEN	t	2026-02-19 05:07:43.906994	2026-02-19 05:07:43.92313	\N
07d7b9eb-3e25-448e-bfd8-fbe48accf91d	Orchestration Cycle 1771477773852	Orchestration Flow Test	Q1	2026	2026-01-01	2026-03-31	OPEN	t	2026-02-19 05:09:37.436126	2026-02-19 05:09:37.453353	\N
b2b2c121-2026-4c4b-807b-02ea654f3430	Orchestration Cycle 1771477851719	Orchestration Flow Test	Q1	2026	2026-01-01	2026-03-31	OPEN	t	2026-02-19 05:10:55.275675	2026-02-19 05:10:55.292466	\N
e8a8c5ae-5234-4ae0-b1a8-39ebe2406d14	Orchestration Cycle 1771478436046	Orchestration Flow Test	Q1	2026	2026-01-01	2026-03-31	OPEN	t	2026-02-19 05:20:39.587317	2026-02-19 05:20:39.604233	\N
59c80357-e720-43fb-ac43-21f886bb6d0c	Orchestration Cycle 1771484428266	Orchestration Flow Test	Q1	2026	2026-01-01	2026-03-31	OPEN	t	2026-02-19 07:00:31.995145	2026-02-19 07:00:32.01206	\N
cb828a67-699d-4f2d-aabf-edd67738d6c3	Orchestration Cycle 1771484536626	Orchestration Flow Test	Q1	2026	2026-01-01	2026-03-31	OPEN	t	2026-02-19 07:02:19.358111	2026-02-19 07:02:19.37485	\N
d87b7106-9ceb-41ba-bfb7-1fa68a5b234c	Lifecycle Cycle 1771492772485	Ultimate Lifecycle Verification	Q1	2026	2026-01-01	2026-12-31	OPEN	t	2026-02-19 09:19:36.31096	2026-02-19 09:19:36.326776	\N
c3681e7a-4909-46d3-bb84-d28b8e0e1f97	Lifecycle Cycle 1771493134135	Ultimate Lifecycle Verification	Q1	2026	2026-01-01	2026-12-31	OPEN	t	2026-02-19 09:25:37.846443	2026-02-19 09:25:37.862304	\N
51379e79-61c3-4fe8-a509-c2ec2fa6b581	Lifecycle Cycle 1771493488203	Ultimate Lifecycle Verification	Q1	2026	2026-01-01	2026-12-31	OPEN	t	2026-02-19 09:31:31.874946	2026-02-19 09:31:31.892135	\N
dbe97880-6df9-4841-bce4-4957c1cd3065	Lifecycle Cycle 1771494666289	Ultimate Lifecycle Verification	Q1	2026	2026-01-01	2026-12-31	OPEN	t	2026-02-19 09:51:09.873633	2026-02-19 09:51:09.891571	\N
8c5fd2de-23eb-4058-98ea-f1046f76a64f	Lifecycle Cycle 1771496587219	Ultimate Lifecycle Verification	Q1	2026	2026-01-01	2026-12-31	OPEN	t	2026-02-19 10:23:10.979758	2026-02-19 10:23:11.000307	\N
7772316e-9d6c-44be-9a15-c9827de126de	Lifecycle Cycle 1771498432770	Ultimate Lifecycle Verification	Q1	2026	2026-01-01	2026-12-31	OPEN	t	2026-02-19 10:53:56.980315	2026-02-19 10:53:56.997398	\N
ab05a53b-182b-4b54-bef7-22c1f4866428	Lifecycle Cycle 1771498552881	Ultimate Lifecycle Verification	Q1	2026	2026-01-01	2026-12-31	OPEN	t	2026-02-19 10:55:57.0648	2026-02-19 10:55:57.081096	\N
a54e6dea-55a2-4683-ac3f-c0d7e84e73d2	Lifecycle Cycle 1771501901228	Ultimate Lifecycle Verification	Q1	2026	2026-01-01	2026-12-31	OPEN	t	2026-02-19 11:51:46.247061	2026-02-19 11:51:46.266621	\N
902d2437-3ba0-4c2c-9651-db170bd3233c	Lifecycle Cycle 1771502319047	Ultimate Lifecycle Verification	Q1	2026	2026-01-01	2026-12-31	OPEN	t	2026-02-19 11:58:44.108158	2026-02-19 11:58:44.130382	\N
72d5acfe-191c-4881-a969-1d133522b223	Lifecycle Cycle 1771502630027	Ultimate Lifecycle Verification	Q1	2026	2026-01-01	2026-12-31	OPEN	t	2026-02-19 12:03:54.826229	2026-02-19 12:03:54.844366	\N
f6cdad56-6c6f-4a0b-b605-4c6ef1fd1945	Lifecycle Cycle 1771502878203	Ultimate Lifecycle Verification	Q1	2026	2026-01-01	2026-12-31	OPEN	t	2026-02-19 12:08:02.840582	2026-02-19 12:08:02.858172	\N
d076a413-fb0d-4600-b2d4-3dbc7a7151e2	Lifecycle Cycle 1771502991180	Ultimate Lifecycle Verification	Q1	2026	2026-01-01	2026-12-31	OPEN	t	2026-02-19 12:09:53.522249	2026-02-19 12:09:53.536606	\N
45cd0cb4-f95d-4574-b3ca-05ae48698b15	Lifecycle Cycle 1771503289645	Ultimate Lifecycle Verification	Q1	2026	2026-01-01	2026-12-31	OPEN	t	2026-02-19 12:14:52.207846	2026-02-19 12:14:52.22279	\N
ede36f79-1f60-4fd0-86d8-25483370d562	Lifecycle Cycle 1771503430852		Q1	2026	2026-01-01	2026-12-31	OPEN	t	2026-02-19 12:17:13.349747	2026-02-19 12:17:13.363775	\N
c9687000-f8cb-42b4-a3a5-7b85b10c33a2	Lifecycle Cycle 1771503480232		Q1	2026	2026-01-01	2026-12-31	OPEN	t	2026-02-19 12:18:02.285225	2026-02-19 12:18:02.299218	\N
b4550ff5-9b7c-49a7-85ec-674deae57b62	Lifecycle Cycle 1771503821341		Q1	2026	2026-01-01	2026-12-31	OPEN	t	2026-02-19 12:23:43.175682	2026-02-19 12:23:43.189758	\N
9d5d3c0f-87e6-44e5-b68c-881e66a8de6b	Lifecycle Cycle 1771503875152		Q1	2026	2026-01-01	2026-12-31	OPEN	t	2026-02-19 12:24:36.933818	2026-02-19 12:24:36.94729	\N
75d8c10d-86f0-4a7b-b702-6954435a174f	Lifecycle Cycle 1771504537951		Q1	2026	2026-01-01	2026-12-31	OPEN	t	2026-02-19 12:35:40.051511	2026-02-19 12:35:40.065758	\N
b9f082c0-5f27-441d-826e-ae0165a3017d	Lifecycle Cycle 1771504556855		Q1	2026	2026-01-01	2026-12-31	OPEN	t	2026-02-19 12:35:58.847906	2026-02-19 12:35:58.861855	\N
dda602b1-f840-4d11-a19c-79a4a283080f	Lifecycle Cycle 1771504865621		Q1	2026	2026-01-01	2026-12-31	OPEN	t	2026-02-19 12:41:07.57903	2026-02-19 12:41:07.593854	\N
587026d1-f118-447e-a281-d609913ed720	Lifecycle Cycle 1771505001047		Q1	2026	2026-01-01	2026-12-31	OPEN	t	2026-02-19 12:43:22.927616	2026-02-19 12:43:22.941971	\N
e52bbc45-ed7c-44d5-ae40-982c531954f8	Lifecycle Cycle 1771505027300		Q1	2026	2026-01-01	2026-12-31	OPEN	t	2026-02-19 12:43:49.037655	2026-02-19 12:43:49.050279	\N
88ef1f71-b763-4e1f-8e20-def74b03b7ad	Lifecycle Cycle 1771505095282		Q1	2026	2026-01-01	2026-12-31	OPEN	t	2026-02-19 12:44:57.048075	2026-02-19 12:44:57.062704	\N
361d08ee-2ba2-48f2-b23d-e773b79afcf3	Lifecycle Cycle 1771505137803		Q1	2026	2026-01-01	2026-12-31	OPEN	t	2026-02-19 12:45:39.614714	2026-02-19 12:45:39.629166	\N
be1ac55c-06bb-4861-b0ba-384fdc9ac6ac	Lifecycle Cycle 1771505204464		Q1	2026	2026-01-01	2026-12-31	OPEN	t	2026-02-19 12:46:46.260337	2026-02-19 12:46:46.274709	\N
754259b7-723e-44a2-88d2-829694142fe2	Lifecycle Cycle 1771505466404		Q1	2026	2026-01-01	2026-12-31	OPEN	t	2026-02-19 12:51:08.240874	2026-02-19 12:51:08.256625	\N
3f3741d0-ce5f-4257-8880-b74240da4e5a	Lifecycle Cycle 1771505516331		Q1	2026	2026-01-01	2026-12-31	OPEN	t	2026-02-19 12:51:58.249814	2026-02-19 12:51:58.2642	\N
629be2f3-85be-4c9c-b878-edd0e941081c	Lifecycle Cycle 1771505633288		Q1	2026	2026-01-01	2026-12-31	OPEN	t	2026-02-19 12:53:55.19549	2026-02-19 12:53:55.210668	\N
c32d1f6d-5bc6-4eb9-b2b2-e41fef732751	Lifecycle Cycle 1771505996095		Q1	2026	2026-01-01	2026-12-31	CLOSED	t	2026-02-19 12:59:58.277896	2026-02-19 13:00:00.029088	\N
ca8351e2-cdfe-4d67-8851-dc6fea83118b	Lifecycle Cycle 1771506052262		Q1	2026	2026-01-01	2026-12-31	CLOSED	t	2026-02-19 13:00:54.471106	2026-02-19 13:00:56.243464	\N
092507ed-7777-4863-9cc2-e1691ea632a6	Launch Cycle 2026	Initial award cycle for system launch.	Q1	2026	2026-02-24	2026-03-26	ACTIVE	t	2026-02-24 05:20:24.601702	2026-02-24 05:20:24.601703	ca93677b-8541-40ea-87a5-05f14c328724
\.


--
-- Data for Name: form_answers; Type: TABLE DATA; Schema: public; Owner: awards_user
--

COPY public.form_answers (id, nomination_id, field_key, value, attachment) FROM stdin;
7ccc6a5e-80ac-45c0-ae49-3da8216b053a	c24b1072-7a0a-40a5-97af-1d12a7b81fc1	impact_score	"5"	\N
10299f1f-1678-45e8-a7ee-761222fde746	c24b1072-7a0a-40a5-97af-1d12a7b81fc1	justification	"Submitting for the ultimate lifecycle test. Exceptional contribution."	\N
006abbf9-5088-4c92-b3ce-aa33a41f24af	e75b3655-c464-4620-b1b9-251326e7259b	impact_score	"5"	\N
10194618-d472-4b26-a8ba-8a4e330c193b	e75b3655-c464-4620-b1b9-251326e7259b	justification	"Submitting for the ultimate lifecycle test. Exceptional contribution."	\N
df1a20ec-356d-4d2c-a3b5-fee634fd9f3a	99693d25-2ff0-47e8-a70d-cb75dae81265	impact_score	"5"	\N
ce954ac5-e6f4-4006-b927-29ab5329e4f0	99693d25-2ff0-47e8-a70d-cb75dae81265	justification	"Submitting for the ultimate lifecycle test. Exceptional contribution."	\N
765e9440-19f7-431a-91e8-32d338438720	13783806-335e-43ac-b679-dff66c3d1bfe	impact_score	"5"	\N
2f02f685-3deb-4b63-8a20-65d38eb29b5e	13783806-335e-43ac-b679-dff66c3d1bfe	justification	"Submitting for the ultimate lifecycle test. Exceptional contribution."	\N
73e96ae9-3f31-4b54-bb35-0fce6c36480e	61b6dc1e-cf17-42bb-9518-fb747825fb2c	impact_score	"5"	\N
f9a08149-5af5-4d70-9b6a-bbb6ab37939c	61b6dc1e-cf17-42bb-9518-fb747825fb2c	justification	"Submitting for the ultimate lifecycle test. Exceptional contribution."	\N
d85dd07d-d656-490f-b10c-d74213f662ee	dd669c7f-0a6d-4ee9-a1a2-5f0f753c7285	impact_score	"5"	\N
4c41e78e-9b2a-4d23-bde6-e823da0eff9c	dd669c7f-0a6d-4ee9-a1a2-5f0f753c7285	justification	"Submitting for the ultimate lifecycle test. Exceptional contribution."	\N
7949a1a6-dbb2-4bcc-92e6-2c402fd19f27	a0fa95e8-1f6d-4259-8af8-b58208cb6a0e	impact_score	"5"	\N
13b15428-3d72-493e-866b-8a4724cf1280	a0fa95e8-1f6d-4259-8af8-b58208cb6a0e	justification	"Submitting for the ultimate lifecycle test. Exceptional contribution."	\N
c6a06993-30ba-4744-aa96-0638d98d5d62	86851325-9102-4da0-bcfe-5b368bd6b288	impact_score	"5"	\N
3c6e5c20-4b06-45c5-94e3-7811fe3c4972	86851325-9102-4da0-bcfe-5b368bd6b288	justification	"Submitting for the ultimate lifecycle test. Exceptional contribution."	\N
99f58280-d9a2-43cc-9508-8fb10bdf8236	f1c7afb8-9a09-4602-9a60-d099bffd4949	performance	"Submitting for the ultimate lifecycle test. Exceptional contribution."	\N
aec09772-0186-40c3-a9ec-ae76f3bf2e18	2385ff0f-3a36-4b83-954f-c15eaa88b6f6	performance	"Submitting for the ultimate lifecycle test. Exceptional contribution."	\N
8f9c9884-14b3-486a-85bd-89669edffd74	9e400795-2f3a-4280-8e1d-aa8819038ea2	performance	"Submitting for the ultimate lifecycle test. Exceptional contribution."	\N
e3d1e990-c72d-4dd3-bf8b-bf5ca3d67f21	4e2d512c-ee42-4353-a413-92ae93ccfd49	performance	"Submitting for the ultimate lifecycle test. Exceptional contribution."	\N
5a09a6f6-035a-496e-bfd6-4f4db8d4521c	db453f37-9918-49cd-91e5-8967d3fafe97	performance	"Submitting for the ultimate lifecycle test. Exceptional contribution."	\N
ed3376f3-48d0-4053-84fa-cddfa0e5e5cb	3aa47f60-dce5-49fb-901f-64e5d59b48e3	performance	"Submitting for the ultimate lifecycle test. Exceptional contribution."	\N
328b6a96-3940-43ef-ada9-17eb9abbd2d0	374d1647-ef3d-4177-9c35-f264329fab76	performance	"Submitting for the ultimate lifecycle test. Exceptional contribution."	\N
\.


--
-- Data for Name: form_fields; Type: TABLE DATA; Schema: public; Owner: awards_user
--

COPY public.form_fields (id, form_id, label, field_key, field_type, is_required, order_index, options, ui_schema, validation, allow_file_upload) FROM stdin;
c19183d9-dab7-4db5-ad56-ab652643f541	8d1766f6-a65c-4864-b328-1c7e5faf5feb	Core Performance	performance_score	RATING	f	0	null	null	null	f
fea6e36f-d620-46a8-8956-21214dd50d5b	71f9b8ea-fbf4-49fa-a2de-c532f3d383b9	Core Performance	performance_score	RATING	f	0	null	null	null	f
c10c855d-e7db-40fb-ae4e-1b0391112b3c	4190d13c-47da-4d2c-9644-0c43c677166d	Core Performance	performance_score	RATING	f	0	null	null	null	f
9cc07e4f-7c51-4bbb-a155-5884efcbca44	da622d5a-6538-4c4d-b7a0-890c9a96cc5e	Core Performance	performance_score	RATING	f	0	null	null	null	f
eaa908d1-0059-4f2b-87cc-269d13cd491a	4342399e-0259-45c4-9a69-cb86a0c57490	Core Performance	performance_score	RATING	f	0	null	null	null	f
d830944f-3f44-4c68-88d3-1e81e9e8d9ff	41a9ec3e-976f-4402-8617-ab6da5c6885e	Core Performance	performance_score	RATING	f	0	null	null	null	f
3fad83f6-f551-4a8b-aed4-c221de00bf98	12aca5b5-adb9-433d-98ef-579b1bc821c3	Core Performance	performance_score	RATING	f	0	null	null	null	f
c88ca402-49ef-4975-9b14-78455f7c60fe	1d551cd0-2bb7-4861-a8d9-ec67f2819e9f	Core Performance	performance_score	RATING	f	0	null	null	null	f
8144053f-338a-481a-82fa-0f6b3f47cff8	663c73b0-75ef-4f9c-80a8-6ee08c19f90c	Impact Score	impact_score	RATING	f	0	null	null	null	f
fdb096cf-95a2-4671-82b7-d3e5436fb6ff	44a51c8d-8720-4df4-8731-fea76097d09c	Impact Score	impact_score	RATING	f	0	null	null	null	f
81e37c0b-a838-470b-809e-a7751002cd3a	f136808c-2bf4-4756-84fd-6db14353cd77	Impact Score	impact_score	RATING	f	0	null	null	null	f
0da04955-1d62-4978-ad1d-599cc7de5c91	8d663b7f-c175-4ebc-943c-a141e7fd092f	Impact Score	impact_score	RATING	f	0	null	null	null	f
fda74821-9a0c-45aa-9786-c85c6b48e50e	7d53198d-bf01-46a3-9e95-ac6666305297	Impact Score	impact_score	RATING	f	0	null	null	null	f
48defc78-b2be-4b47-9603-60c459064b59	7d53198d-bf01-46a3-9e95-ac6666305297	Justification	justification	TEXTAREA	f	1	null	null	null	f
ccc7fd8a-c945-437e-9f00-5efd41f29bc0	91e620b2-7d63-4ded-b0fc-b7b142d90961	Impact Score	impact_score	RATING	f	0	null	null	null	f
f23dd452-399e-4536-8b89-6f4fb587b57a	91e620b2-7d63-4ded-b0fc-b7b142d90961	Justification	justification	TEXTAREA	f	1	null	null	null	f
a26ba942-446b-4375-b1d4-b900361626ea	55bc7f94-aefa-432c-862d-c10ac588e0e9	Impact Score	impact_score	RATING	f	0	null	null	null	f
596658dd-26b7-4700-a649-852fcedb8b34	55bc7f94-aefa-432c-862d-c10ac588e0e9	Justification	justification	TEXTAREA	f	1	null	null	null	f
0da259f5-db72-4ad0-941a-1a9ad8366e63	19b70abe-07e5-45cb-82cc-252a3dc0c20c	Impact Score	impact_score	RATING	f	0	null	null	null	f
5b139a99-b6dd-499e-8497-733ef26877e7	19b70abe-07e5-45cb-82cc-252a3dc0c20c	Justification	justification	TEXTAREA	f	1	null	null	null	f
b0336d11-1f19-40aa-8432-a905575273b4	d8c05c16-7c26-4f36-bde0-ee6d14f72748	Impact Score	impact_score	RATING	f	0	null	null	null	f
152d5569-67cc-4c37-9334-bf7b1ff9eb8b	d8c05c16-7c26-4f36-bde0-ee6d14f72748	Justification	justification	TEXTAREA	f	1	null	null	null	f
10d6ab27-8464-4750-ac5e-ffe532b2906d	1b47426b-641c-4613-88d5-28b0cae486b3	Impact Score	impact_score	RATING	f	0	null	null	null	f
82075411-429c-4ee2-98f4-96c0905e69b2	1b47426b-641c-4613-88d5-28b0cae486b3	Justification	justification	TEXTAREA	f	1	null	null	null	f
1ec79e06-d169-4373-ac1d-fb9ca74857f2	bdf61018-c7b7-4f6f-b0d4-50c298645e75	Impact Score	impact_score	RATING	f	0	null	null	null	f
8a395b79-2f09-4fd1-8aa2-0f26ece22d71	bdf61018-c7b7-4f6f-b0d4-50c298645e75	Justification	justification	TEXTAREA	f	1	null	null	null	f
5e6f04d9-a7b0-4bd1-ace4-5755dcb0b465	c3d6b569-d525-4d96-984e-1c5433ff4799	Impact Score	impact_score	RATING	f	0	null	null	null	f
d552d026-16f7-470d-91ab-aa052f12c11c	c3d6b569-d525-4d96-984e-1c5433ff4799	Justification	justification	TEXTAREA	f	1	null	null	null	f
f1fbfbcc-051e-418e-a0eb-5e6ce49db58f	a42e3d52-13b3-4254-807b-c18bd6f21cdf	Impact Score	impact_score	RATING	f	0	null	null	null	f
a96d5981-a8c1-4299-9b98-74b62fb4f19d	a42e3d52-13b3-4254-807b-c18bd6f21cdf	Justification	justification	TEXTAREA	f	1	null	null	null	f
bae74541-4b59-4393-9a5e-dab34ea35280	e8dc91e5-918b-48d9-958e-575da359c006	Impact Score	impact_score	RATING	f	0	null	null	null	f
5d29f961-e24e-4271-82ba-b12a75e9d5f9	e8dc91e5-918b-48d9-958e-575da359c006	Justification	justification	TEXTAREA	f	1	null	null	null	f
5687a9d9-0d4e-40d8-ab8b-ee5048f84213	fbaaa9b1-3825-4928-9688-f432c72560eb	Performance	performance	TEXT	f	0	null	null	null	f
59fb6f3f-454f-4ea8-8c2c-0d587c76a3c2	d005d0de-6e9d-40c7-a35b-d540403dc70d	Performance	performance	TEXT	f	0	null	null	null	f
38b66a69-1025-472b-a5d8-699e7c69fe0e	57c71b81-4d27-4c93-8f87-729ab295e443	Performance	performance	TEXT	f	0	null	null	null	f
f83ba793-136a-4805-97d5-c3c33dbe54df	e505d453-d56c-4e0c-984d-2a938087bae2	Performance	performance	TEXT	f	0	null	null	null	f
1d97941e-defb-4bca-9360-230a15fa56fb	359165e2-37a5-4baf-bf14-215a989891ff	Performance	performance	TEXT	f	0	null	null	null	f
99f52b0c-7d40-4fa9-8dc0-083f2dbc6709	11447479-b89b-4f92-9b8c-a1ff06f42412	Performance	performance	TEXT	f	0	null	null	null	f
021b8c12-142b-404e-a378-864ecfd2b9eb	7f8b66cc-85a6-48d0-a31c-dd49e9392db2	Performance	performance	TEXT	f	0	null	null	null	f
aec45bd5-519c-4868-8065-75556bdcd44c	01b729ae-b00b-4a1a-9f7e-4451467936c5	Performance	performance	TEXT	f	0	null	null	null	f
d7fb6fb2-220c-44d0-aba6-cca41f9ad65f	ae005145-cd79-4aaf-be69-a520ed87f403	Performance	performance	TEXT	f	0	null	null	null	f
2dcf6695-9809-441d-b525-45643e16913a	15524ff5-5126-41f7-8d0f-6653c57a10b3	Performance	performance	TEXT	f	0	null	null	null	f
03088270-1c86-41f4-b88f-9796a2a7ff74	fd7d57be-e55d-45f1-9316-f230152897eb	Performance	performance	TEXT	f	0	null	null	null	f
ced41fb3-4d51-4da3-a3ae-f95e8166279b	ed5a692c-aead-43f7-ad2b-b562fbd237b4	Performance	performance	TEXT	f	0	null	null	null	f
587011c0-eea7-4a7c-8fa6-1e8ac27701dc	c772c470-ff3e-49fc-a461-ba53b06f4549	Performance	performance	TEXT	f	0	null	null	null	f
3ff3a6a2-7a01-45ba-a531-52a8e73f4284	bb0fb151-d295-46c8-9bcf-0c2642e40685	Performance	performance	TEXT	f	0	null	null	null	f
ccb63040-2edb-4cea-b496-3c47b80e978a	daf33af4-f7a5-4ea8-8592-d0c0ed17a422	Performance	performance	TEXT	f	0	null	null	null	f
e21b796d-e3da-4d5d-83e0-cdbbdd7822c0	fe10e812-4cdf-48e7-8624-ca37ecac7f6d	Performance	performance	TEXT	f	0	null	null	null	f
719dda94-7ee5-48a0-b8d8-bb55fdc7c8cb	c6896719-aed8-4f35-a244-6ca86ea3d537	Performance	performance	TEXT	f	0	null	null	null	f
d931e3b2-e2e4-4361-b42a-5fce3d2506c0	37a4a17f-88e3-4134-a7d0-55f88a133938	Performance	performance	TEXT	f	0	null	null	null	f
413e881a-c526-4e4c-91da-732cb1d33399	0fcf7490-4f85-4291-b363-1d2daa89d762	Summary of Achievement	achievement_summary	TEXTAREA	t	1	\N	\N	\N	f
9ef29b44-e3df-44ea-b746-53cfd5e020c3	0fcf7490-4f85-4291-b363-1d2daa89d762	Collaboration Impact	collaboration	RATING	t	2	\N	\N	\N	f
1395ee47-c07b-46b6-819a-5166f3642709	0fcf7490-4f85-4291-b363-1d2daa89d762	Supporting Documents	documents	FILE	f	3	\N	\N	\N	f
\.


--
-- Data for Name: forms; Type: TABLE DATA; Schema: public; Owner: awards_user
--

COPY public.forms (id, name, description, is_active, created_at, category) FROM stdin;
8d1766f6-a65c-4864-b328-1c7e5faf5feb	Orchestration Criteria 1771477269053	Automated criteria for orchestration flow.	t	2026-02-19 05:01:10.958275	\N
71f9b8ea-fbf4-49fa-a2de-c532f3d383b9	Orchestration Criteria 1771477409162	Automated criteria for orchestration flow.	t	2026-02-19 05:03:31.021401	\N
4190d13c-47da-4d2c-9644-0c43c677166d	Orchestration Criteria 1771477660404	Automated criteria for orchestration flow.	t	2026-02-19 05:07:42.259498	\N
da622d5a-6538-4c4d-b7a0-890c9a96cc5e	Orchestration Criteria 1771477773852	Automated criteria for orchestration flow.	t	2026-02-19 05:09:35.778508	\N
4342399e-0259-45c4-9a69-cb86a0c57490	Orchestration Criteria 1771477851719	Automated criteria for orchestration flow.	t	2026-02-19 05:10:53.616389	\N
41a9ec3e-976f-4402-8617-ab6da5c6885e	Orchestration Criteria 1771478436046	Automated criteria for orchestration flow.	t	2026-02-19 05:20:37.938707	\N
12aca5b5-adb9-433d-98ef-579b1bc821c3	Orchestration Criteria 1771484428266	Automated criteria for orchestration flow.	t	2026-02-19 07:00:30.240898	\N
1d551cd0-2bb7-4861-a8d9-ec67f2819e9f	Orchestration Criteria 1771484536626	Automated criteria for orchestration flow.	t	2026-02-19 07:02:18.496569	\N
663c73b0-75ef-4f9c-80a8-6ee08c19f90c	Lifecycle Criteria 1771492586282	Evaluation criteria for the ultimate lifecycle test.	t	2026-02-19 09:16:28.743292	\N
44a51c8d-8720-4df4-8731-fea76097d09c	Lifecycle Criteria 1771492772485	Evaluation criteria for the ultimate lifecycle test.	t	2026-02-19 09:19:34.430378	\N
f136808c-2bf4-4756-84fd-6db14353cd77	Lifecycle Criteria 1771493134135	Evaluation criteria for the ultimate lifecycle test.	t	2026-02-19 09:25:36.136179	\N
8d663b7f-c175-4ebc-943c-a141e7fd092f	Lifecycle Criteria 1771493488203	Evaluation criteria for the ultimate lifecycle test.	t	2026-02-19 09:31:30.187317	\N
7d53198d-bf01-46a3-9e95-ac6666305297	Lifecycle Criteria 1771494666289	Evaluation criteria for the ultimate lifecycle test.	t	2026-02-19 09:51:08.184363	\N
91e620b2-7d63-4ded-b0fc-b7b142d90961	Lifecycle Criteria 1771496587219	Evaluation criteria for the ultimate lifecycle test.	t	2026-02-19 10:23:09.2559	\N
55bc7f94-aefa-432c-862d-c10ac588e0e9	Lifecycle Criteria 1771498432770	Evaluation criteria for the ultimate lifecycle test.	t	2026-02-19 10:53:55.313836	\N
19b70abe-07e5-45cb-82cc-252a3dc0c20c	Lifecycle Criteria 1771498552881	Evaluation criteria for the ultimate lifecycle test.	t	2026-02-19 10:55:55.359139	\N
d8c05c16-7c26-4f36-bde0-ee6d14f72748	Lifecycle Criteria 1771501901228	Evaluation criteria for the ultimate lifecycle test.	t	2026-02-19 11:51:44.218247	\N
1b47426b-641c-4613-88d5-28b0cae486b3	Lifecycle Criteria 1771502319047	Evaluation criteria for the ultimate lifecycle test.	t	2026-02-19 11:58:42.077777	\N
bdf61018-c7b7-4f6f-b0d4-50c298645e75	Lifecycle Criteria 1771502630027	Evaluation criteria for the ultimate lifecycle test.	t	2026-02-19 12:03:52.840683	\N
c3d6b569-d525-4d96-984e-1c5433ff4799	Lifecycle Criteria 1771502878203	Evaluation criteria for the ultimate lifecycle test.	t	2026-02-19 12:08:00.869137	\N
a42e3d52-13b3-4254-807b-c18bd6f21cdf	Lifecycle Criteria 1771502991180	Evaluation criteria for the ultimate lifecycle test.	t	2026-02-19 12:09:52.685263	\N
e8dc91e5-918b-48d9-958e-575da359c006	Lifecycle Criteria 1771503289645	Evaluation criteria for the ultimate lifecycle test.	t	2026-02-19 12:14:51.354736	\N
fbaaa9b1-3825-4928-9688-f432c72560eb	Lifecycle Criteria 1771503430852	Ultimate lifecycle E2E testing criteria	t	2026-02-19 12:17:12.493753	\N
d005d0de-6e9d-40c7-a35b-d540403dc70d	Lifecycle Criteria 1771503458350	Ultimate lifecycle E2E testing criteria	t	2026-02-19 12:17:39.914751	\N
57c71b81-4d27-4c93-8f87-729ab295e443	Lifecycle Criteria 1771503480232	Ultimate lifecycle E2E testing criteria	t	2026-02-19 12:18:01.558744	\N
e505d453-d56c-4e0c-984d-2a938087bae2	Lifecycle Criteria 1771503821341	Ultimate lifecycle E2E testing criteria	t	2026-02-19 12:23:42.459296	\N
359165e2-37a5-4baf-bf14-215a989891ff	Lifecycle Criteria 1771503875152	Ultimate lifecycle E2E testing criteria	t	2026-02-19 12:24:36.217539	\N
11447479-b89b-4f92-9b8c-a1ff06f42412	Lifecycle Criteria 1771504537951	Ultimate lifecycle E2E testing criteria	t	2026-02-19 12:35:39.323064	\N
7f8b66cc-85a6-48d0-a31c-dd49e9392db2	Lifecycle Criteria 1771504556855	Ultimate lifecycle E2E testing criteria	t	2026-02-19 12:35:58.088236	\N
01b729ae-b00b-4a1a-9f7e-4451467936c5	Lifecycle Criteria 1771504865621	Ultimate lifecycle E2E testing criteria	t	2026-02-19 12:41:06.852387	\N
ae005145-cd79-4aaf-be69-a520ed87f403	Lifecycle Criteria 1771505001047	Ultimate lifecycle E2E testing criteria	t	2026-02-19 12:43:22.183104	\N
15524ff5-5126-41f7-8d0f-6653c57a10b3	Lifecycle Criteria 1771505027300	Ultimate lifecycle E2E testing criteria	t	2026-02-19 12:43:48.325501	\N
fd7d57be-e55d-45f1-9316-f230152897eb	Lifecycle Criteria 1771505095282	Ultimate lifecycle E2E testing criteria	t	2026-02-19 12:44:56.343145	\N
ed5a692c-aead-43f7-ad2b-b562fbd237b4	Lifecycle Criteria 1771505137803	Ultimate lifecycle E2E testing criteria	t	2026-02-19 12:45:38.885247	\N
c772c470-ff3e-49fc-a461-ba53b06f4549	Lifecycle Criteria 1771505204464	Ultimate lifecycle E2E testing criteria	t	2026-02-19 12:46:45.556222	\N
bb0fb151-d295-46c8-9bcf-0c2642e40685	Lifecycle Criteria 1771505466404	Ultimate lifecycle E2E testing criteria	t	2026-02-19 12:51:07.517931	\N
daf33af4-f7a5-4ea8-8592-d0c0ed17a422	Lifecycle Criteria 1771505516331	Ultimate lifecycle E2E testing criteria	t	2026-02-19 12:51:57.483429	\N
fe10e812-4cdf-48e7-8624-ca37ecac7f6d	Lifecycle Criteria 1771505633288	Ultimate lifecycle E2E testing criteria	t	2026-02-19 12:53:54.477984	\N
c6896719-aed8-4f35-a244-6ca86ea3d537	Lifecycle Criteria 1771505996095	Ultimate lifecycle E2E testing criteria	t	2026-02-19 12:59:57.571912	\N
37a4a17f-88e3-4134-a7d0-55f88a133938	Lifecycle Criteria 1771506052262	Ultimate lifecycle E2E testing criteria	t	2026-02-19 13:00:53.742642	\N
0fcf7490-4f85-4291-b363-1d2daa89d762	Standard Nomination Form	General nomination form for excellence and peer awards.	t	2026-02-24 05:20:24.605878	GENERAL
\.


--
-- Data for Name: nominations; Type: TABLE DATA; Schema: public; Owner: awards_user
--

COPY public.nominations (id, cycle_id, form_id, nominee_id, nominated_by_id, status, submitted_at, created_at, updated_at) FROM stdin;
c24b1072-7a0a-40a5-97af-1d12a7b81fc1	7772316e-9d6c-44be-9a15-c9827de126de	55bc7f94-aefa-432c-862d-c10ac588e0e9	1cc7dab7-d466-482e-aa51-293f3684fcbb	2144eff6-7d8e-431f-80f2-5111260e6f71	SUBMITTED	2026-02-19 10:54:00.773431	2026-02-19 10:54:00.77735	2026-02-19 10:54:00.777352
e75b3655-c464-4620-b1b9-251326e7259b	ab05a53b-182b-4b54-bef7-22c1f4866428	19b70abe-07e5-45cb-82cc-252a3dc0c20c	1cc7dab7-d466-482e-aa51-293f3684fcbb	2144eff6-7d8e-431f-80f2-5111260e6f71	SUBMITTED	2026-02-19 10:56:00.856224	2026-02-19 10:56:00.856524	2026-02-19 10:56:00.856526
99693d25-2ff0-47e8-a70d-cb75dae81265	a54e6dea-55a2-4683-ac3f-c0d7e84e73d2	d8c05c16-7c26-4f36-bde0-ee6d14f72748	1cc7dab7-d466-482e-aa51-293f3684fcbb	2144eff6-7d8e-431f-80f2-5111260e6f71	SUBMITTED	2026-02-19 11:51:50.29736	2026-02-19 11:51:50.29775	2026-02-19 11:51:50.297755
13783806-335e-43ac-b679-dff66c3d1bfe	902d2437-3ba0-4c2c-9651-db170bd3233c	1b47426b-641c-4613-88d5-28b0cae486b3	1cc7dab7-d466-482e-aa51-293f3684fcbb	2144eff6-7d8e-431f-80f2-5111260e6f71	SUBMITTED	2026-02-19 11:58:48.141944	2026-02-19 11:58:48.142245	2026-02-19 11:58:48.142247
61b6dc1e-cf17-42bb-9518-fb747825fb2c	72d5acfe-191c-4881-a969-1d133522b223	bdf61018-c7b7-4f6f-b0d4-50c298645e75	1cc7dab7-d466-482e-aa51-293f3684fcbb	2144eff6-7d8e-431f-80f2-5111260e6f71	SUBMITTED	2026-02-19 12:03:58.836247	2026-02-19 12:03:58.836628	2026-02-19 12:03:58.836629
dd669c7f-0a6d-4ee9-a1a2-5f0f753c7285	f6cdad56-6c6f-4a0b-b605-4c6ef1fd1945	c3d6b569-d525-4d96-984e-1c5433ff4799	1cc7dab7-d466-482e-aa51-293f3684fcbb	2144eff6-7d8e-431f-80f2-5111260e6f71	SUBMITTED	2026-02-19 12:08:06.85381	2026-02-19 12:08:06.854145	2026-02-19 12:08:06.854147
a0fa95e8-1f6d-4259-8af8-b58208cb6a0e	d076a413-fb0d-4600-b2d4-3dbc7a7151e2	a42e3d52-13b3-4254-807b-c18bd6f21cdf	1cc7dab7-d466-482e-aa51-293f3684fcbb	2144eff6-7d8e-431f-80f2-5111260e6f71	SUBMITTED	2026-02-19 12:09:56.459411	2026-02-19 12:09:56.459658	2026-02-19 12:09:56.459659
86851325-9102-4da0-bcfe-5b368bd6b288	45cd0cb4-f95d-4574-b3ca-05ae48698b15	e8dc91e5-918b-48d9-958e-575da359c006	1cc7dab7-d466-482e-aa51-293f3684fcbb	2144eff6-7d8e-431f-80f2-5111260e6f71	SUBMITTED	2026-02-19 12:14:55.18071	2026-02-19 12:14:55.181085	2026-02-19 12:14:55.181087
f1c7afb8-9a09-4602-9a60-d099bffd4949	361d08ee-2ba2-48f2-b23d-e773b79afcf3	ed5a692c-aead-43f7-ad2b-b562fbd237b4	1cc7dab7-d466-482e-aa51-293f3684fcbb	2144eff6-7d8e-431f-80f2-5111260e6f71	SUBMITTED	2026-02-19 12:45:40.411661	2026-02-19 12:45:40.411937	2026-02-19 12:45:40.411938
2385ff0f-3a36-4b83-954f-c15eaa88b6f6	be1ac55c-06bb-4861-b0ba-384fdc9ac6ac	c772c470-ff3e-49fc-a461-ba53b06f4549	1cc7dab7-d466-482e-aa51-293f3684fcbb	2144eff6-7d8e-431f-80f2-5111260e6f71	SUBMITTED	2026-02-19 12:46:47.04884	2026-02-19 12:46:47.049174	2026-02-19 12:46:47.049176
9e400795-2f3a-4280-8e1d-aa8819038ea2	754259b7-723e-44a2-88d2-829694142fe2	bb0fb151-d295-46c8-9bcf-0c2642e40685	1cc7dab7-d466-482e-aa51-293f3684fcbb	2144eff6-7d8e-431f-80f2-5111260e6f71	SUBMITTED	2026-02-19 12:51:09.031879	2026-02-19 12:51:09.032116	2026-02-19 12:51:09.032117
4e2d512c-ee42-4353-a413-92ae93ccfd49	3f3741d0-ce5f-4257-8880-b74240da4e5a	daf33af4-f7a5-4ea8-8592-d0c0ed17a422	1cc7dab7-d466-482e-aa51-293f3684fcbb	2144eff6-7d8e-431f-80f2-5111260e6f71	SUBMITTED	2026-02-19 12:51:59.090689	2026-02-19 12:51:59.090956	2026-02-19 12:51:59.090957
3aa47f60-dce5-49fb-901f-64e5d59b48e3	c32d1f6d-5bc6-4eb9-b2b2-e41fef732751	c6896719-aed8-4f35-a244-6ca86ea3d537	1cc7dab7-d466-482e-aa51-293f3684fcbb	2144eff6-7d8e-431f-80f2-5111260e6f71	SUBMITTED	2026-02-19 12:59:59.083152	2026-02-19 12:59:59.084236	2026-02-19 12:59:59.084238
374d1647-ef3d-4177-9c35-f264329fab76	ca8351e2-cdfe-4d67-8851-dc6fea83118b	37a4a17f-88e3-4134-a7d0-55f88a133938	1cc7dab7-d466-482e-aa51-293f3684fcbb	2144eff6-7d8e-431f-80f2-5111260e6f71	SUBMITTED	2026-02-19 13:00:55.278256	2026-02-19 13:00:55.278501	2026-02-19 13:00:55.278502
db453f37-9918-49cd-91e5-8967d3fafe97	629be2f3-85be-4c9c-b878-edd0e941081c	fe10e812-4cdf-48e7-8624-ca37ecac7f6d	1cc7dab7-d466-482e-aa51-293f3684fcbb	2144eff6-7d8e-431f-80f2-5111260e6f71	PANEL_REVIEW	2026-02-19 12:53:55.983033	2026-02-19 12:53:55.98326	2026-02-19 14:47:44.296632
\.


--
-- Data for Name: panel_assignments; Type: TABLE DATA; Schema: public; Owner: awards_user
--

COPY public.panel_assignments (id, nomination_id, panel_id, assigned_by, status, assigned_at, completed_at) FROM stdin;
48767403-3b5c-4cf4-b763-a96636e7506a	db453f37-9918-49cd-91e5-8967d3fafe97	f28b1d02-32c4-45e1-b3dd-06b41b881111	368e5aec-bba7-40e4-95dc-361416fad403	PENDING	2026-02-19 14:47:44.291973+00	\N
\.


--
-- Data for Name: panel_members; Type: TABLE DATA; Schema: public; Owner: awards_user
--

COPY public.panel_members (id, panel_id, user_id, role, created_at) FROM stdin;
8751f913-5f6e-4bd6-ae90-7c73db86fb68	f28b1d02-32c4-45e1-b3dd-06b41b881111	a2e41139-002e-4204-86b4-5c6a1ce3c1d3	REVIEWER	2026-02-19 14:58:11.172677+00
\.


--
-- Data for Name: panel_reviews; Type: TABLE DATA; Schema: public; Owner: awards_user
--

COPY public.panel_reviews (id, panel_assignment_id, panel_member_id, panel_task_id, score, comment, reviewed_at) FROM stdin;
\.


--
-- Data for Name: panel_tasks; Type: TABLE DATA; Schema: public; Owner: awards_user
--

COPY public.panel_tasks (id, panel_id, title, description, max_score, order_index, is_required, criteria_field_id) FROM stdin;
af48275a-1319-4960-ad2f-2591bfea0c0c	f28b1d02-32c4-45e1-b3dd-06b41b881111	Performance		5	0	t	d931e3b2-e2e4-4361-b42a-5fce3d2506c0
7479755f-65e5-4100-b0e8-5294eccba556	f28b1d02-32c4-45e1-b3dd-06b41b881111	Performance		5	0	t	e21b796d-e3da-4d5d-83e0-cdbbdd7822c0
21c7e756-db14-4b17-bc9d-2373410fbb68	f28b1d02-32c4-45e1-b3dd-06b41b881111	Core Performance		5	0	t	c88ca402-49ef-4975-9b14-78455f7c60fe
\.


--
-- Data for Name: panels; Type: TABLE DATA; Schema: public; Owner: awards_user
--

COPY public.panels (id, name, description, is_active, created_at) FROM stdin;
b924fe58-0c48-4f60-89b8-5ee712163345	Lifecycle Panel 1771498432770		t	2026-02-19 10:54:02.405049+00
74394883-a9f9-470d-972f-f65c8b1acf83	Lifecycle Panel 1771498552881		t	2026-02-19 10:56:02.520441+00
87e52b38-b70c-4808-82a8-5cb5418e333f	Lifecycle Panel 1771501901228		t	2026-02-19 11:51:52.300466+00
f1f5f30c-8859-4845-9833-c2f695603b6a	Lifecycle Panel 1771505996095		t	2026-02-19 13:00:00.752525+00
f28b1d02-32c4-45e1-b3dd-06b41b881111	Lifecycle Panel 1771506052262		t	2026-02-19 13:00:56.91973+00
\.


--
-- Data for Name: security_questions; Type: TABLE DATA; Schema: public; Owner: awards_user
--

COPY public.security_questions (id, user_id, question, answer_hash) FROM stdin;
e63fdc90-ba00-4f48-9275-be7c59789671	38e00a47-20ef-4e76-be65-5fabeaccad36	What is your pet's name?	$2b$12$TdWsTJ5gglCNcbSxrxTihucrbepL6nECFNhq.AUU7E8.AqTNNJG9i
9580fd0b-691e-4ab0-adb4-18d6e1a66a99	38e00a47-20ef-4e76-be65-5fabeaccad36	What city were you born in?	$2b$12$GgzIKNOyNGSy1WBVfSSjM.4O7Abpe0JahBGAqSsX2pkfp.lpELrmK
1588e748-65f0-488c-8aec-336eb3540b91	38e00a47-20ef-4e76-be65-5fabeaccad36	What is your favorite color?	$2b$12$g6moY4Gb2lfw.QrotemO/e9fLrYPrlPm4Vk2uE8LvpcNt.FghxP3.
ba3a9cb5-515f-40f6-990f-0893e1079890	368e5aec-bba7-40e4-95dc-361416fad403	What was the name of your first school?	$2b$12$kESRTBnc1uJOWfolRyY4AO2kDCFaw8kQQyDXJRd3R4mQ6aLn3/nXO
653ec65b-84b3-487f-9a2c-71e7241c5254	368e5aec-bba7-40e4-95dc-361416fad403	What is your favorite food?	$2b$12$bAjE2X/sWkf8T9FuPKrQvOQeJznNaLkHNdAXVKzDVBIFP6BStOZJ2
29baa28c-b5a7-44e9-988a-059c310d30d7	368e5aec-bba7-40e4-95dc-361416fad403	What city were you born in?	$2b$12$yDtD/vzla.HoP15W0qvJNOjARiG01heY4O52qIDHD/x5D06oolccy
15f2160e-8968-41b6-b68a-8b8a81bc57fb	2144eff6-7d8e-431f-80f2-5111260e6f71	What was the name of your first school?	$2b$12$QWn/0jzpOOSLD6TF3E8EuephfSs2wbgryEsVqloj0Rr0ygFLxJs32
6c862ffd-d1ed-4be9-88b6-acbb7dd4a53a	2144eff6-7d8e-431f-80f2-5111260e6f71	What is your favorite food?	$2b$12$xBFkNPsxTtfwZUjlzE2gr.yLQdh9eMaQnCaI/gf6kp.pN7aFB7NBy
9cb321f4-2ed0-485d-bf3d-a0e64b2cbac8	2144eff6-7d8e-431f-80f2-5111260e6f71	What city were you born in?	$2b$12$y/IutSPUe6thu7lTSaSS2.Ib6c/YCM4hMCq2iHfJ0PNvcs8KSm0Gi
77b7ef0d-b1c9-4a7b-9ecd-ff42759779e7	a2e41139-002e-4204-86b4-5c6a1ce3c1d3	What was the name of your first school?	$2b$12$Ddtf6woB3iwBcNLbCQSfqudnkOTwWFiF9rdojRtHhmTEWcE/uJGfu
8da74d06-3037-4775-bcdc-0d205fd3aeb4	a2e41139-002e-4204-86b4-5c6a1ce3c1d3	What is your favorite food?	$2b$12$dgcfpT1bo5dg8D9wrJm9Xu0kCdkly1WdJgijtm6i2JYw29eeII.ei
d3bdb14a-64ab-49db-9efe-697fd544af5a	a2e41139-002e-4204-86b4-5c6a1ce3c1d3	What city were you born in?	$2b$12$.7ZqNb7GiQj4ukv2ngjIOeWA.Oa84QGhr9APJP4QH9hFFkxQI2SsG
c11621cd-71ce-4f4f-9f29-a04e3b47ef45	1cc7dab7-d466-482e-aa51-293f3684fcbb	What was the name of your first school?	$2b$12$Ambag5rpAEU7kUmpEpvs4eksks9QvxWT2S8Dt1EoHo7HubNuFdQWu
ef40a507-8e6a-4a1c-91dd-c2ef7e018462	1cc7dab7-d466-482e-aa51-293f3684fcbb	What is your favorite food?	$2b$12$O.COoJCI2UlolDRB7bdZs.qm3wuf6/tXvB6E76KMRKXDdINPNeikS
9cdeb72c-c422-41dc-b381-8838e16410c0	1cc7dab7-d466-482e-aa51-293f3684fcbb	What city were you born in?	$2b$12$9OtyPHYJ2htNumL/PWx3FezB..hG2Pqg90d8PySZ/zc0yvUdXmtJO
32d43053-cf86-435f-9106-a493ed1ab56d	b0255b1e-383b-431d-9028-359324eaf475	What was the name of your first school?	$2b$12$qUFylqipMyrUNYZKdQLLDutPbbZ9N18wWkpAdb.wVKIFLWJ0zXT.W
933c9f1d-f6e2-4ad9-bc70-0d7afe076388	b0255b1e-383b-431d-9028-359324eaf475	What is your favorite food?	$2b$12$yRxiObTbWuzkaMYAT06Pzu/y0iGkc0GmW4RjgOTa9lvOmw4T9lhmi
a7be567a-d9cb-4a9a-aa11-6d4fc9200790	b0255b1e-383b-431d-9028-359324eaf475	What city were you born in?	$2b$12$6yDs43KrQC0bsKJoKnhWfePkneQMg7B3gfnhfe/kac0th8w5Q0bOa
\.


--
-- Data for Name: users; Type: TABLE DATA; Schema: public; Owner: awards_user
--

COPY public.users (id, employee_code, name, email, password_hash, role, is_active, delete_requested_at, deleted_at, profile_image, created_at) FROM stdin;
38e00a47-20ef-4e76-be65-5fabeaccad36	\N	System Admin	admin@company.com	$2b$12$QuMC4YA038yGHF3hvSr69uw9ly1IfmC8I3n4qejXb9vjGYRhClzZW	SUPER_ADMIN	t	\N	\N	\N	2026-02-18 18:33:54.121725
368e5aec-bba7-40e4-95dc-361416fad403	\N	HR Admin	hr.admin@example.com	$2b$12$bxRcJO54nIrFQ.3dlB0RvuFijowG2SPdV/JJq//tnBC4B8vJBjcEa	HR	t	\N	\N	\N	2026-02-19 04:52:07.022986
2144eff6-7d8e-431f-80f2-5111260e6f71	\N	Line Manager	manager@example.com	$2b$12$NrrBFevlHMRb/X3ZSKW4tO4Ly7oADYwL6RjqQvfwKR.lWA1eRicHG	MANAGER	t	\N	\N	\N	2026-02-19 04:52:07.825865
a2e41139-002e-4204-86b4-5c6a1ce3c1d3	\N	Panel Member	panel@example.com	$2b$12$O45NhCBzA6XpAo0LP/cWa.bpElo4zmGI4oE1pm/5jlkmeNjPy6DY.	PANEL	t	\N	\N	\N	2026-02-19 04:52:08.718334
1cc7dab7-d466-482e-aa51-293f3684fcbb	\N	Employee One	employee1@example.com	$2b$12$mT8tvdsNK2v4E3cZlHk73u0z995jfLnY8EFEKymATxN8iwdp9I.Je	EMPLOYEE	t	\N	\N	\N	2026-02-19 04:52:09.540642
b0255b1e-383b-431d-9028-359324eaf475	\N	Employee Two	employee2@example.com	$2b$12$6EcgJT7SulBjG2n7ShPwmOxa8mrDSeZ2o293FQKlhX/sWIDxZacXm	EMPLOYEE	t	\N	\N	\N	2026-02-19 04:52:10.40931
\.


--
-- Name: alembic_version alembic_version_pkc; Type: CONSTRAINT; Schema: public; Owner: awards_user
--

ALTER TABLE ONLY public.alembic_version
    ADD CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num);


--
-- Name: award_types award_types_pkey; Type: CONSTRAINT; Schema: public; Owner: awards_user
--

ALTER TABLE ONLY public.award_types
    ADD CONSTRAINT award_types_pkey PRIMARY KEY (id);


--
-- Name: awards awards_pkey; Type: CONSTRAINT; Schema: public; Owner: awards_user
--

ALTER TABLE ONLY public.awards
    ADD CONSTRAINT awards_pkey PRIMARY KEY (id);


--
-- Name: cycles cycles_pkey; Type: CONSTRAINT; Schema: public; Owner: awards_user
--

ALTER TABLE ONLY public.cycles
    ADD CONSTRAINT cycles_pkey PRIMARY KEY (id);


--
-- Name: form_answers form_answers_pkey; Type: CONSTRAINT; Schema: public; Owner: awards_user
--

ALTER TABLE ONLY public.form_answers
    ADD CONSTRAINT form_answers_pkey PRIMARY KEY (id);


--
-- Name: form_fields form_fields_pkey; Type: CONSTRAINT; Schema: public; Owner: awards_user
--

ALTER TABLE ONLY public.form_fields
    ADD CONSTRAINT form_fields_pkey PRIMARY KEY (id);


--
-- Name: forms forms_pkey; Type: CONSTRAINT; Schema: public; Owner: awards_user
--

ALTER TABLE ONLY public.forms
    ADD CONSTRAINT forms_pkey PRIMARY KEY (id);


--
-- Name: nominations nominations_pkey; Type: CONSTRAINT; Schema: public; Owner: awards_user
--

ALTER TABLE ONLY public.nominations
    ADD CONSTRAINT nominations_pkey PRIMARY KEY (id);


--
-- Name: panel_assignments panel_assignments_pkey; Type: CONSTRAINT; Schema: public; Owner: awards_user
--

ALTER TABLE ONLY public.panel_assignments
    ADD CONSTRAINT panel_assignments_pkey PRIMARY KEY (id);


--
-- Name: panel_members panel_members_pkey; Type: CONSTRAINT; Schema: public; Owner: awards_user
--

ALTER TABLE ONLY public.panel_members
    ADD CONSTRAINT panel_members_pkey PRIMARY KEY (id);


--
-- Name: panel_reviews panel_reviews_pkey; Type: CONSTRAINT; Schema: public; Owner: awards_user
--

ALTER TABLE ONLY public.panel_reviews
    ADD CONSTRAINT panel_reviews_pkey PRIMARY KEY (id);


--
-- Name: panel_tasks panel_tasks_pkey; Type: CONSTRAINT; Schema: public; Owner: awards_user
--

ALTER TABLE ONLY public.panel_tasks
    ADD CONSTRAINT panel_tasks_pkey PRIMARY KEY (id);


--
-- Name: panels panels_pkey; Type: CONSTRAINT; Schema: public; Owner: awards_user
--

ALTER TABLE ONLY public.panels
    ADD CONSTRAINT panels_pkey PRIMARY KEY (id);


--
-- Name: security_questions security_questions_pkey; Type: CONSTRAINT; Schema: public; Owner: awards_user
--

ALTER TABLE ONLY public.security_questions
    ADD CONSTRAINT security_questions_pkey PRIMARY KEY (id);


--
-- Name: panel_members uq_panel_member; Type: CONSTRAINT; Schema: public; Owner: awards_user
--

ALTER TABLE ONLY public.panel_members
    ADD CONSTRAINT uq_panel_member UNIQUE (panel_id, user_id);


--
-- Name: panel_reviews uq_unique_task_review; Type: CONSTRAINT; Schema: public; Owner: awards_user
--

ALTER TABLE ONLY public.panel_reviews
    ADD CONSTRAINT uq_unique_task_review UNIQUE (panel_assignment_id, panel_member_id, panel_task_id);


--
-- Name: users users_pkey; Type: CONSTRAINT; Schema: public; Owner: awards_user
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (id);


--
-- Name: ix_award_types_code; Type: INDEX; Schema: public; Owner: awards_user
--

CREATE UNIQUE INDEX ix_award_types_code ON public.award_types USING btree (code);


--
-- Name: ix_users_email; Type: INDEX; Schema: public; Owner: awards_user
--

CREATE UNIQUE INDEX ix_users_email ON public.users USING btree (email);


--
-- Name: ix_users_employee_code; Type: INDEX; Schema: public; Owner: awards_user
--

CREATE UNIQUE INDEX ix_users_employee_code ON public.users USING btree (employee_code);


--
-- Name: awards awards_award_type_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: awards_user
--

ALTER TABLE ONLY public.awards
    ADD CONSTRAINT awards_award_type_id_fkey FOREIGN KEY (award_type_id) REFERENCES public.award_types(id);


--
-- Name: awards awards_cycle_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: awards_user
--

ALTER TABLE ONLY public.awards
    ADD CONSTRAINT awards_cycle_id_fkey FOREIGN KEY (cycle_id) REFERENCES public.cycles(id);


--
-- Name: awards awards_nomination_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: awards_user
--

ALTER TABLE ONLY public.awards
    ADD CONSTRAINT awards_nomination_id_fkey FOREIGN KEY (nomination_id) REFERENCES public.nominations(id);


--
-- Name: awards awards_winner_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: awards_user
--

ALTER TABLE ONLY public.awards
    ADD CONSTRAINT awards_winner_id_fkey FOREIGN KEY (winner_id) REFERENCES public.users(id);


--
-- Name: cycles fk_cycles_award_type_id; Type: FK CONSTRAINT; Schema: public; Owner: awards_user
--

ALTER TABLE ONLY public.cycles
    ADD CONSTRAINT fk_cycles_award_type_id FOREIGN KEY (award_type_id) REFERENCES public.award_types(id);


--
-- Name: form_answers form_answers_nomination_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: awards_user
--

ALTER TABLE ONLY public.form_answers
    ADD CONSTRAINT form_answers_nomination_id_fkey FOREIGN KEY (nomination_id) REFERENCES public.nominations(id) ON DELETE CASCADE;


--
-- Name: form_fields form_fields_form_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: awards_user
--

ALTER TABLE ONLY public.form_fields
    ADD CONSTRAINT form_fields_form_id_fkey FOREIGN KEY (form_id) REFERENCES public.forms(id) ON DELETE CASCADE;


--
-- Name: nominations nominations_cycle_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: awards_user
--

ALTER TABLE ONLY public.nominations
    ADD CONSTRAINT nominations_cycle_id_fkey FOREIGN KEY (cycle_id) REFERENCES public.cycles(id);


--
-- Name: nominations nominations_form_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: awards_user
--

ALTER TABLE ONLY public.nominations
    ADD CONSTRAINT nominations_form_id_fkey FOREIGN KEY (form_id) REFERENCES public.forms(id);


--
-- Name: nominations nominations_nominated_by_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: awards_user
--

ALTER TABLE ONLY public.nominations
    ADD CONSTRAINT nominations_nominated_by_id_fkey FOREIGN KEY (nominated_by_id) REFERENCES public.users(id);


--
-- Name: nominations nominations_nominee_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: awards_user
--

ALTER TABLE ONLY public.nominations
    ADD CONSTRAINT nominations_nominee_id_fkey FOREIGN KEY (nominee_id) REFERENCES public.users(id);


--
-- Name: panel_assignments panel_assignments_assigned_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: awards_user
--

ALTER TABLE ONLY public.panel_assignments
    ADD CONSTRAINT panel_assignments_assigned_by_fkey FOREIGN KEY (assigned_by) REFERENCES public.users(id);


--
-- Name: panel_assignments panel_assignments_nomination_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: awards_user
--

ALTER TABLE ONLY public.panel_assignments
    ADD CONSTRAINT panel_assignments_nomination_id_fkey FOREIGN KEY (nomination_id) REFERENCES public.nominations(id);


--
-- Name: panel_assignments panel_assignments_panel_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: awards_user
--

ALTER TABLE ONLY public.panel_assignments
    ADD CONSTRAINT panel_assignments_panel_id_fkey FOREIGN KEY (panel_id) REFERENCES public.panels(id);


--
-- Name: panel_members panel_members_panel_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: awards_user
--

ALTER TABLE ONLY public.panel_members
    ADD CONSTRAINT panel_members_panel_id_fkey FOREIGN KEY (panel_id) REFERENCES public.panels(id);


--
-- Name: panel_members panel_members_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: awards_user
--

ALTER TABLE ONLY public.panel_members
    ADD CONSTRAINT panel_members_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- Name: panel_reviews panel_reviews_panel_assignment_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: awards_user
--

ALTER TABLE ONLY public.panel_reviews
    ADD CONSTRAINT panel_reviews_panel_assignment_id_fkey FOREIGN KEY (panel_assignment_id) REFERENCES public.panel_assignments(id) ON DELETE CASCADE;


--
-- Name: panel_reviews panel_reviews_panel_member_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: awards_user
--

ALTER TABLE ONLY public.panel_reviews
    ADD CONSTRAINT panel_reviews_panel_member_id_fkey FOREIGN KEY (panel_member_id) REFERENCES public.panel_members(id) ON DELETE CASCADE;


--
-- Name: panel_reviews panel_reviews_panel_task_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: awards_user
--

ALTER TABLE ONLY public.panel_reviews
    ADD CONSTRAINT panel_reviews_panel_task_id_fkey FOREIGN KEY (panel_task_id) REFERENCES public.panel_tasks(id) ON DELETE CASCADE;


--
-- Name: panel_tasks panel_tasks_panel_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: awards_user
--

ALTER TABLE ONLY public.panel_tasks
    ADD CONSTRAINT panel_tasks_panel_id_fkey FOREIGN KEY (panel_id) REFERENCES public.panels(id);


--
-- Name: security_questions security_questions_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: awards_user
--

ALTER TABLE ONLY public.security_questions
    ADD CONSTRAINT security_questions_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: SCHEMA public; Type: ACL; Schema: -; Owner: awards_user
--

REVOKE USAGE ON SCHEMA public FROM PUBLIC;


--
-- PostgreSQL database dump complete
--

\unrestrict 00gEnQyT8VHgMpnfro5yBaJyxwZ8ahFyg3EcTCWzFoI0ELmjbJfdlAfGiZHM83Y

