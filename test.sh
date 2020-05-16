# CI test script

python -m flake8 --statistics || exit $?
if [ ! -z "$TEST_BOT_TOKEN" ]; then
  PHONE=+999662$(printf "%04d" $((RANDOM / 10)))
  printf '%d\n%s\n' 6 eb06d4abfb49dc3eeb1aeb98ae0f581e > api_token.txt
  python -m friendly-telegram --phone "$TEST_BOT_TOKEN" --phone "$PHONE" --test-dc=22222 --no-web --self-test || exit $?
else
  echo 'Skipping unit tests due to missing bot token ($TEST_BOT_TOKEN is empty)'
fi
exit 0
