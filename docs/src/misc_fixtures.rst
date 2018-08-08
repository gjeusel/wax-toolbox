Miscelleneous Fixtures
----------------------

Miscelleneous fixtures contains tools for easy testing on python requests
using `Betamax <http://betamax.readthedocs.io/en/latest/index.html>`_.

Usage
~~~~~

**In conf.py\:**

.. code:: python

    import betamax
    from wax_toolbox.misc_fixtures import sanitize_token, RecorderBase

    from betamax_serializers import pretty_json

    CASSETTES_DIR = Path(__file__).parent / 'cassettes'
    SAMPLES_DIR = Path(__file__).parent / 'samples'

    # Betamax configuration:
    with betamax.Betamax.configure() as config:
        config.cassette_library_dir = CASSETTES_DIR.as_posix()
        betamax.Betamax.register_serializer(pretty_json.PrettyJSONSerializer)
        config.default_cassette_options['serialize_with'] = 'prettyjson'
        config.before_record(callback=sanitize_token)
        # config.default_cassette_options['match_requests_on'].extend([
        #     'json_body'
        # ])


    def pytest_addoption(parser):
        parser.addoption('--generate-samples', action='store_true', default=False,
                        help='''Generate cassettes & samples for new tests.
                        The existing ones will remain unchanged.''')
        parser.addoption('--regenerate-samples', action='store_true', default=False,
                        help='Regenerate cassettes & samples for all tests.')

    @pytest.fixture(scope='session')
    def recorder(request):
        BETAMAX_MODE = 'none'  # test existing cassettes
        if request.config.getoption("--generate-samples"):  # generate samples and cassettes for new tests
            BETAMAX_MODE = 'once'
        if request.config.getoption("--regenerate-samples"):  # regenerate samples and cassettes for all tests
            BETAMAX_MODE = 'all'

        class Recorder(RecorderBase):
            def __init__(self, bucket_name, session=requests.Session()):
                super().__init__(bucket_name=bucket_name,
                                sample_dir=SAMPLE_DIR
                                session=session,
                                betamax_mode=BETAMAX_MODE
                                )

        yield Recorder


    @pytest.fixture(scope='session', params=[
        # Old ones:
        (pd.Timestamp('2016-01-01T00:00:00', tz='CET'),
        pd.Timestamp('2016-01-03T00:00:00', tz='CET')),

        # DST change winter -> summer:
        (pd.Timestamp('2017-03-26T00:00:00', tz='CET'),
        pd.Timestamp('2017-03-27T00:00:00', tz='CET')),

        # DST change summer -> winter:
        (pd.Timestamp('2017-10-29T00:00:00', tz='CET'),
        pd.Timestamp('2017-10-30T00:00:00', tz='CET')),

        # Early 2018:
        (pd.Timestamp('2018-01-21T00:00:00', tz='UTC'),
        pd.Timestamp('2018-01-23T00:00:00', tz='CET')),

    ])
    def period(request):
        dct = {'start': request.param[0], 'end': request.param[1]}
        return dct

**Then in some test_api.py\:**

.. code:: python

    def test_api(period, recorder):
        client = InitClientApi()

        bucket_name = "api_endpoint_{}_{}".format(
            period['start'].strftime(dtformat),
            period['end'].strftime(dtformat),
        )

        with recorder(bucket_name=bucket_name, session=client.session) as r:
            df = client.get_total_load_forecast(**period)
            r.send_dataframe(df)


.. automodule:: wax_toolbox.misc_fixtures
    :members:
